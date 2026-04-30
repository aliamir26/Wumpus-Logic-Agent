"""
knowledge_base.py
─────────────────
The Knowledge Base (KB) for the Wumpus World agent.

The KB stores propositional logic sentences as CNF clauses and provides
two core operations:

  TELL(sentence) → add what the agent perceives/knows into the KB
  ASK(query)     → query whether a fact is entailed by the KB

Variable naming convention:
  P_{r}_{c}  → Pit exists at (row r, col c)
  W_{r}_{c}  → Wumpus exists at (row r, col c)
  B_{r}_{c}  → Breeze perceived at (row r, col c)
  S_{r}_{c}  → Stench perceived at (row r, col c)
  V_{r}_{c}  → Cell (r, c) has been visited
  SAFE_{r}_{c} → Cell (r, c) is known safe

All cells use 1-based indexing to match the classic Wumpus World convention.
"""

from __future__ import annotations
from app.logic.resolution import (
    biconditional_to_cnf,
    unit_clause,
    negate,
    is_cell_safe,
    resolution_entails,
)


class KnowledgeBase:
    """
    Propositional Logic Knowledge Base backed by CNF clause storage.

    Attributes
    ----------
    clauses      : list[frozenset]  — all CNF clauses in the KB
    total_steps  : int              — cumulative resolution inference steps
    grid_size    : int              — N for an N×N grid
    """

    def __init__(self, grid_size: int):
        self.grid_size   = grid_size
        self.clauses: list[frozenset] = []
        self.total_steps: int = 0

        # Bootstrap: the agent starts at (1,1) which is ALWAYS safe
        self._add_initial_facts()

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _in_bounds(self, r: int, c: int) -> bool:
        return 1 <= r <= self.grid_size and 1 <= c <= self.grid_size

    def _add_clause(self, clause: frozenset) -> None:
        """Add a clause if it's not already known."""
        if clause not in self.clauses:
            self.clauses.append(clause)

    def _add_clauses(self, clauses: list[frozenset]) -> None:
        for cl in clauses:
            self._add_clause(cl)

    def _neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        """Return the 4-directional in-bounds neighbors of cell (r, c)."""
        candidates = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        return [(nr, nc) for nr, nc in candidates if self._in_bounds(nr, nc)]

    # ──────────────────────────────────────────────────────────────────────
    # Bootstrap facts
    # ──────────────────────────────────────────────────────────────────────

    def _add_initial_facts(self) -> None:
        """
        The starting cell (1,1) is guaranteed safe — no Pit, no Wumpus.
        Also add the general rule: there is exactly one Wumpus somewhere
        (we don't need to enumerate all cells for moderate complexity).
        """
        # No pit at start
        self._add_clause(unit_clause("~P_1_1"))
        # No wumpus at start
        self._add_clause(unit_clause("~W_1_1"))

    # ──────────────────────────────────────────────────────────────────────
    # TELL — add percepts and derived rules to the KB
    # ──────────────────────────────────────────────────────────────────────

    def tell_visited(self, r: int, c: int) -> None:
        """Mark cell (r, c) as visited — it can't have a Pit or Wumpus."""
        self._add_clause(unit_clause(f"~P_{r}_{c}"))
        self._add_clause(unit_clause(f"~W_{r}_{c}"))
        self._add_clause(unit_clause(f"V_{r}_{c}"))

    def tell_breeze(self, r: int, c: int, has_breeze: bool) -> None:
        """
        Tell the KB whether a Breeze was perceived at (r, c).

        Biconditional rule:
          B_{r}_{c} ↔ (P_{r-1}_{c} ∨ P_{r+1}_{c} ∨ P_{r}_{c-1} ∨ P_{r}_{c+1})

        If no breeze → we know none of the neighbors have a pit.
        If breeze    → at least one neighbor has a pit (we don't know which).
        """
        neighbors = self._neighbors(r, c)
        pit_lits  = [f"P_{nr}_{nc}" for nr, nc in neighbors]

        if has_breeze:
            # Assert B_{r}_{c} = True
            self._add_clause(unit_clause(f"B_{r}_{c}"))
            # Add the biconditional CNF expansion
            self._add_clauses(biconditional_to_cnf(f"B_{r}_{c}", pit_lits))
        else:
            # Assert B_{r}_{c} = False
            self._add_clause(unit_clause(f"~B_{r}_{c}"))
            # No breeze → NO neighbor has a pit
            for lit in pit_lits:
                self._add_clause(unit_clause(f"~{lit}"))

    def tell_stench(self, r: int, c: int, has_stench: bool) -> None:
        """
        Tell the KB whether a Stench was perceived at (r, c).

        Biconditional rule:
          S_{r}_{c} ↔ (W_{r-1}_{c} ∨ W_{r+1}_{c} ∨ W_{r}_{c-1} ∨ W_{r}_{c+1})
        """
        neighbors  = self._neighbors(r, c)
        wump_lits  = [f"W_{nr}_{nc}" for nr, nc in neighbors]

        if has_stench:
            self._add_clause(unit_clause(f"S_{r}_{c}"))
            self._add_clauses(biconditional_to_cnf(f"S_{r}_{c}", wump_lits))
        else:
            self._add_clause(unit_clause(f"~S_{r}_{c}"))
            for lit in wump_lits:
                self._add_clause(unit_clause(f"~{lit}"))

    def tell_percepts(self, r: int, c: int, breeze: bool, stench: bool) -> None:
        """Convenience: tell the KB all percepts received at (r, c)."""
        self.tell_visited(r, c)
        self.tell_breeze(r, c, breeze)
        self.tell_stench(r, c, stench)

    # ──────────────────────────────────────────────────────────────────────
    # ASK — query the KB
    # ──────────────────────────────────────────────────────────────────────

    def ask_safe(self, r: int, c: int) -> bool:
        """
        ASK: Is cell (r, c) provably safe (no pit, no wumpus)?

        Uses Resolution Refutation internally. Updates total_steps.
        Returns True if the cell is proven safe.
        """
        safe, steps = is_cell_safe(self.clauses, r, c)
        self.total_steps += steps
        return safe

    def ask_pit(self, r: int, c: int) -> bool:
        """ASK: Is a Pit at (r, c) entailed by the KB? (Danger detection)"""
        entailed, steps = resolution_entails(self.clauses, f"P_{r}_{c}")
        self.total_steps += steps
        return entailed

    def ask_wumpus(self, r: int, c: int) -> bool:
        """ASK: Is the Wumpus at (r, c) entailed by the KB?"""
        entailed, steps = resolution_entails(self.clauses, f"W_{r}_{c}")
        self.total_steps += steps
        return entailed

    # ──────────────────────────────────────────────────────────────────────
    # Snapshot for debugging / educational display
    # ──────────────────────────────────────────────────────────────────────

    def clause_count(self) -> int:
        return len(self.clauses)

    def dump_clauses(self) -> list[str]:
        """Return clauses as readable strings (for debug panel)."""
        return [str(set(cl)) for cl in self.clauses[:50]]  # cap at 50 for display
