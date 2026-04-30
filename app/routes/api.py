"""
api.py
──────
FastAPI route definitions for the Wumpus Logic Agent.

Endpoints:
  POST /api/new_game          — start a fresh game
  GET  /api/state             — get current game state
  POST /api/move              — manually move the agent
  POST /api/ai_step           — let AI take one step
  POST /api/ai_solve          — let AI run until done (max N steps)
  GET  /api/reveal            — reveal ground truth (for game over screen)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.logic.agent import WumpusWorld, WumpusAgent, GameStatus

router = APIRouter()

# ──────────────────────────────────────────────────────────────────────────────
# In-memory session store (single session for simplicity)
# In production you'd use Redis or a database.
# ──────────────────────────────────────────────────────────────────────────────

_game: dict = {
    "world": None,
    "agent": None,
}


def _require_game() -> WumpusAgent:
    if _game["agent"] is None:
        raise HTTPException(status_code=400, detail="No active game. Start a new game first.")
    return _game["agent"]


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response schemas
# ──────────────────────────────────────────────────────────────────────────────

class NewGameRequest(BaseModel):
    size: int = Field(default=6, ge=4, le=8, description="Grid size N for an N×N world")
    pit_probability: float = Field(default=0.15, ge=0.05, le=0.25)


class MoveRequest(BaseModel):
    row: int
    col: int


class SolveRequest(BaseModel):
    max_steps: int = Field(default=50, ge=1, le=200)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/new_game")
def new_game(req: NewGameRequest):
    """
    Initialize a fresh Wumpus World and a new KB-based agent.
    Returns the initial game state.
    """
    world = WumpusWorld(size=req.size, pit_probability=req.pit_probability)
    agent = WumpusAgent(world)

    _game["world"] = world
    _game["agent"] = agent

    return {
        "message": "New game started!",
        "state": agent.get_state(),
    }


@router.get("/state")
def get_state():
    """Return the current game state without changing anything."""
    agent = _require_game()
    return agent.get_state()


@router.post("/move")
def manual_move(req: MoveRequest):
    """
    Manually move the agent to the specified (row, col).
    The move is NOT validated against the KB — the player takes the risk.
    """
    agent = _require_game()

    if agent.status != GameStatus.PLAYING:
        return {"error": "Game is over", "state": agent.get_state()}

    state = agent.move_to(req.row, req.col)
    return {"state": state}


@router.post("/ai_step")
def ai_step():
    """
    Let the AI agent autonomously take ONE step.
    Uses the KB to pick the safest available move.
    """
    agent = _require_game()

    if agent.status != GameStatus.PLAYING:
        return {"error": "Game is over", "state": agent.get_state()}

    state = agent.ai_step()
    return {"state": state}


@router.post("/ai_solve")
def ai_solve(req: SolveRequest):
    """
    Run the AI agent for up to `max_steps` steps automatically.
    Returns the final state + a list of intermediate states for animation.
    """
    agent = _require_game()

    if agent.status != GameStatus.PLAYING:
        return {"error": "Game is over", "state": agent.get_state()}

    states = []
    for _ in range(req.max_steps):
        if agent.status != GameStatus.PLAYING:
            break
        agent.ai_step()
        states.append(agent.get_state())

    return {
        "states": states,
        "final_state": agent.get_state(),
        "steps_taken": len(states),
    }


@router.get("/reveal")
def reveal():
    """
    Reveal the hidden ground truth (Wumpus/Pit positions).
    Called after game over to show what was really there.
    """
    agent = _require_game()
    return {
        "ground_truth": agent.get_reveal(),
        "state": agent.get_state(),
    }
