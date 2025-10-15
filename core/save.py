# core/saveio.py
import json, os
from dataclasses import asdict
from core.types import *

def serialize(state: GameState) -> dict:
    d = {
        "width": state.width, "height": state.height,
        "mines": list(state.mines),
        "revealed": list(state.revealed),
        "flags": list(state.flags),
        "enemy_hp": state.enemy_hp, "enemy_max_hp": state.enemy_max_hp,
        "total_mines_target": state.total_mines_target,
        "turn": state.turn.name, "phase": state.phase.name, "outcome": state.outcome.name,
        "rng_seed": state.rng_seed, "version": state.version,
        # grid dump (minimal fields)
        "grid": [[{"state": cell.state.name, "has_mine": cell.has_mine, "number": cell.number}
                  for cell in row] for row in state.grid],
    }
    return d

def deserialize(d: dict) -> GameState:
    grid = [[Cell(state=CellState[cell["state"]], has_mine=cell["has_mine"], number=cell["number"])
             for cell in row] for row in d["grid"]]
    return GameState(
        width=d["width"], height=d["height"], grid=grid,
        mines=set(map(tuple, d["mines"])),
        revealed=set(map(tuple, d["revealed"])),
        flags=set(map(tuple, d["flags"])),
        enemy_hp=d["enemy_hp"], enemy_max_hp=d["enemy_max_hp"],
        total_mines_target=d["total_mines_target"],
        turn=Turn[d["turn"]], phase=Phase[d["phase"]], outcome=Outcome[d["outcome"]],
        rng_seed=d["rng_seed"], version=d.get("version",1)
    )

def save_state(state: GameState, path="save.json"):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(serialize(state), f, separators=(",", ":"))
    os.replace(tmp, path)

def load_state(path="save.json") -> GameState:
    with open(path, "r", encoding="utf-8") as f:
        return deserialize(json.load(f))
