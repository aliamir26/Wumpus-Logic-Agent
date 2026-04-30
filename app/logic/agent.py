"""
agent.py
────────
The Wumpus World environment + the Knowledge-Based Agent.

Two classes:
  WumpusWorld  — holds the ground truth grid (Wumpus, Pits, Gold positions).
                 The agent NEVER has direct access to this — it only sees percepts.

  WumpusAgent  — the KB-based agent. It maintains its own KB and decides moves.
"""

from __future__ import annotations
import random
from enum import Enum
from app.logic.knowledge_base import KnowledgeBase


# ──────────────────────────────────────────────────────────────────────────────
# Enums & constants
# ──────────────────────────────────────────────────────────────────────────────

class GameStatus(str, Enum):
    PLAYING  = "playing"
    WON      = "won"
    DEAD_PIT = "dead_pit"
    DEAD_WUMPUS = "dead_wumpus"


class CellKnowledge(str, Enum):
    """What the agent believes about a cell (for UI coloring)."""
    UNKNOWN    = "unknown"    # grey  — never visited, no info
    VISITED    = "visited"    # green — confirmed safe & visited
    SAFE       = "safe"       # teal  — proven safe but not yet visited
    DANGEROUS  = "dangerous"  # red   — believed dangerous
    CURRENT    = "current"    # yellow/orange — agent is here right now


# ──────────────────────────────────────────────────────────────────────────────
# Wumpus World (hidden ground truth)
# ──────────────────────────────────────────────────────────────────────────────

class WumpusWorld:
    """
    Generates and stores the hidden ground truth of the Wumpus World.

    The agent NEVER reads from this directly.
    Only `get_percepts()` is the interface — simulating the environment.
    """

    def __init__(self, size: int, pit_probability: float = 0.15):
        self.size = size
        self.pits: set[tuple[int,int]]  = set()
        self.wumpus: tuple[int,int]     = (0, 0)
        self.gold: tuple[int,int]       = (0, 0)
        self._generate(pit_probability)

    def _generate(self, pit_prob: float) -> None:
        """Randomly place Wumpus, Gold, and Pits. (1,1) is always free."""
        size = self.size

        # All cells except (1,1)
        all_cells = [
            (r, c)
            for r in range(1, size+1)
            for c in range(1, size+1)
            if (r, c) != (1, 1)
        ]
        random.shuffle(all_cells)

        # Place Wumpus
        self.wumpus = all_cells.pop()

        # Place Gold
        self.gold = all_cells.pop()

        # Place Pits with given probability on remaining cells
        for cell in all_cells:
            if random.random() < pit_prob:
                self.pits.add(cell)

    def _neighbors(self, r: int, c: int) -> list[tuple[int,int]]:
        candidates = [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
        return [(nr,nc) for nr,nc in candidates
                if 1 <= nr <= self.size and 1 <= nc <= self.size]

    def get_percepts(self, r: int, c: int) -> dict:
        """
        Return what the agent perceives at cell (r, c):
          - breeze : any adjacent cell has a pit
          - stench : any adjacent cell has the wumpus
          - glitter: gold is in this cell
          - bump   : (handled by agent movement logic)
        """
        neighbors = self._neighbors(r, c)
        breeze  = any(n in self.pits    for n in neighbors)
        stench  = any(n == self.wumpus  for n in neighbors)
        glitter = (r, c) == self.gold
        death   = (r, c) in self.pits or (r, c) == self.wumpus
        cause   = None
        if (r, c) in self.pits:
            cause = "pit"
        elif (r, c) == self.wumpus:
            cause = "wumpus"

        return {
            "breeze" : breeze,
            "stench" : stench,
            "glitter": glitter,
            "death"  : death,
            "cause"  : cause,
        }

    def to_reveal_dict(self) -> dict:
        """Return ground truth for 'game over' reveal."""
        return {
            "wumpus": list(self.wumpus),
            "pits"  : [list(p) for p in self.pits],
            "gold"  : list(self.gold),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Knowledge-Based Agent
# ──────────────────────────────────────────────────────────────────────────────

class WumpusAgent:
    """
    A propositional-logic-based agent that navigates the Wumpus World.

    The agent:
      1. Visits a cell → receives percepts from the environment.
      2. TELLs the KB about the percepts.
      3. ASKs the KB which adjacent cells are safe.
      4. Moves to a safe unvisited cell if possible.
      5. Falls back to least-risky unvisited cell if no provably safe move.
    """

    def __init__(self, world: WumpusWorld):
        self.world       = world
        self.size        = world.size
        self.kb          = KnowledgeBase(world.size)
        self.pos         : tuple[int,int] = (1, 1)
        self.visited     : set[tuple[int,int]] = set()
        self.safe_cells  : set[tuple[int,int]] = set()   # proven safe by KB
        self.status      : GameStatus           = GameStatus.PLAYING
        self.last_percepts: dict                = {}
        self.move_history: list[tuple[int,int]] = []
        self.gold_found  : bool                 = False

        # Process starting cell
        self._process_current_cell()

    # ──────────────────────────────────────────────────────────────────────
    # Core step
    # ──────────────────────────────────────────────────────────────────────

    def _process_current_cell(self) -> None:
        """Sense percepts, update KB, check win/death."""
        r, c = self.pos
        percepts = self.world.get_percepts(r, c)
        self.last_percepts = percepts
        self.visited.add(self.pos)
        self.safe_cells.add(self.pos)
        self.move_history.append(self.pos)

        # Check death
        if percepts["death"]:
            if percepts["cause"] == "pit":
                self.status = GameStatus.DEAD_PIT
            else:
                self.status = GameStatus.DEAD_WUMPUS
            return

        # Check gold
        if percepts["glitter"]:
            self.gold_found = True
            self.status = GameStatus.WON
            return

        # Tell KB
        self.kb.tell_percepts(r, c, percepts["breeze"], percepts["stench"])

        # Update safe_cells from KB inference
        self._update_safe_cells()

    def _update_safe_cells(self) -> None:
        """Ask the KB about all unvisited cells and mark confirmed-safe ones."""
        for r in range(1, self.size+1):
            for c in range(1, self.size+1):
                if (r, c) not in self.visited and (r, c) not in self.safe_cells:
                    if self.kb.ask_safe(r, c):
                        self.safe_cells.add((r, c))

    def _neighbors(self, r: int, c: int) -> list[tuple[int,int]]:
        candidates = [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
        return [(nr,nc) for nr,nc in candidates
                if 1 <= nr <= self.size and 1 <= nc <= self.size]

    # ──────────────────────────────────────────────────────────────────────
    # Movement
    # ──────────────────────────────────────────────────────────────────────

    def move_to(self, r: int, c: int) -> dict:
        """
        Attempt to move the agent to (r, c).
        Returns a state dict for the API response.
        """
        if self.status != GameStatus.PLAYING:
            return self.get_state()

        if not (1 <= r <= self.size and 1 <= c <= self.size):
            return {**self.get_state(), "error": "Out of bounds"}

        self.pos = (r, c)
        self._process_current_cell()
        return self.get_state()

    def ai_step(self) -> dict:
        """
        Let the agent choose one move autonomously.

        Priority order:
          1. Unvisited safe cell adjacent to current position (KB-proven).
          2. Any unvisited safe cell (backtrack if needed — simplified).
          3. Random unvisited neighbor (frontier exploration, risky).
        """
        if self.status != GameStatus.PLAYING:
            return self.get_state()

        r, c = self.pos

        # Option 1: Safe unvisited neighbor
        neighbors = self._neighbors(r, c)
        safe_unvisited_neighbors = [
            n for n in neighbors
            if n in self.safe_cells and n not in self.visited
        ]
        if safe_unvisited_neighbors:
            target = safe_unvisited_neighbors[0]
            return self.move_to(*target)

        # Option 2: Any safe unvisited cell (teleport-style for simplicity)
        safe_unvisited = [
            cell for cell in self.safe_cells
            if cell not in self.visited
        ]
        if safe_unvisited:
            # Prefer cells reachable from current position (BFS)
            target = self._bfs_nearest(safe_unvisited)
            if target:
                # Move one step toward target
                next_step = self._bfs_step_toward(self.pos, target)
                if next_step:
                    return self.move_to(*next_step)

        # Option 3: Frontier move (risky — no proven safe cell exists)
        unvisited_neighbors = [n for n in neighbors if n not in self.visited]
        if unvisited_neighbors:
            # Pick one that is not KNOWN dangerous
            for candidate in unvisited_neighbors:
                if not self.kb.ask_pit(*candidate) and not self.kb.ask_wumpus(*candidate):
                    return self.move_to(*candidate)
            # All risky — pick randomly as last resort
            return self.move_to(*random.choice(unvisited_neighbors))

        # No moves possible — agent is stuck (shouldn't happen in most grids)
        return {**self.get_state(), "message": "No moves available"}

    def _bfs_nearest(self, targets: list[tuple]) -> tuple | None:
        """BFS from current position to find the nearest target cell."""
        from collections import deque
        queue = deque([(self.pos, [])])
        visited_bfs: set = {self.pos}

        while queue:
            cell, path = queue.popleft()
            if cell in targets:
                return cell
            for neighbor in self._neighbors(*cell):
                if neighbor not in visited_bfs:
                    # Only traverse through visited (safe) cells
                    if neighbor in self.visited or neighbor in self.safe_cells:
                        visited_bfs.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        return None

    def _bfs_step_toward(self, start: tuple, goal: tuple) -> tuple | None:
        """Return the first step on the BFS shortest path from start to goal."""
        from collections import deque
        queue = deque([(start, [])])
        visited_bfs: set = {start}

        while queue:
            cell, path = queue.popleft()
            if cell == goal:
                return path[0] if path else None
            for neighbor in self._neighbors(*cell):
                if neighbor not in visited_bfs:
                    if neighbor in self.visited or neighbor in self.safe_cells:
                        visited_bfs.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        return None

    # ──────────────────────────────────────────────────────────────────────
    # State serialization (for API)
    # ──────────────────────────────────────────────────────────────────────

    def get_cell_knowledge(self, r: int, c: int) -> str:
        """Return the agent's belief about cell (r, c) for UI coloring."""
        if (r, c) == self.pos:
            return CellKnowledge.CURRENT
        if (r, c) in self.visited:
            return CellKnowledge.VISITED
        if (r, c) in self.safe_cells:
            return CellKnowledge.SAFE
        return CellKnowledge.UNKNOWN

    def get_state(self) -> dict:
        """Serialize full game state for the frontend."""
        grid = []
        for r in range(1, self.size+1):
            row = []
            for c in range(1, self.size+1):
                cell = {
                    "r": r,
                    "c": c,
                    "knowledge": self.get_cell_knowledge(r, c),
                    "visited": (r, c) in self.visited,
                    "safe": (r, c) in self.safe_cells,
                }
                # Add percepts for the current cell
                if (r, c) == self.pos:
                    cell["breeze"]  = self.last_percepts.get("breeze", False)
                    cell["stench"]  = self.last_percepts.get("stench", False)
                    cell["glitter"] = self.last_percepts.get("glitter", False)
                row.append(cell)
            grid.append(row)

        return {
            "grid"          : grid,
            "agent_pos"     : list(self.pos),
            "size"          : self.size,
            "status"        : self.status.value,
            "visited_count" : len(self.visited),
            "safe_count"    : len(self.safe_cells),
            "inference_steps": self.kb.total_steps,
            "clause_count"  : self.kb.clause_count(),
            "percepts"      : self.last_percepts,
            "gold_found"    : self.gold_found,
            "move_count"    : len(self.move_history),
        }

    def get_reveal(self) -> dict:
        """Return ground truth for game over reveal."""
        return self.world.to_reveal_dict()
