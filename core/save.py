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
        "ai_reveals_remaining": state.ai_reveals_remaining,
        "mine_stock": state.mine_stock,
        "recover_stock": state.recover_stock,
        "player_action_mode": state.player_action_mode,
        "last_enemy_move": None if state.last_enemy_move is None else {
            "kind": state.last_enemy_move.kind,
            "pos": list(state.last_enemy_move.pos),
            "chosen_p": state.last_enemy_move.chosen_p,
            "rationale": state.last_enemy_move.rationale,
        },
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
    last_enemy_move = None
    if d.get("last_enemy_move") is not None:
        m = d["last_enemy_move"]
        last_enemy_move = Move(
            kind=m["kind"],
            pos=tuple(m["pos"]),
            chosen_p=m.get("chosen_p", 0.0),
            rationale=m.get("rationale", ""),
        )
    return GameState(
        width=d["width"], height=d["height"], grid=grid,
        mines=set(map(tuple, d["mines"])),
        revealed=set(map(tuple, d["revealed"])),
        flags=set(map(tuple, d["flags"])),
        enemy_hp=d["enemy_hp"], enemy_max_hp=d["enemy_max_hp"],
        ai_reveals_remaining=d.get("ai_reveals_remaining", 0),
        mine_stock=d.get("mine_stock", 1),
        recover_stock=d.get("recover_stock", 10),
        player_action_mode=d.get("player_action_mode", "PLACE"),
        total_mines_target=d["total_mines_target"],
        turn=Turn[d["turn"]], phase=Phase[d["phase"]], outcome=Outcome[d["outcome"]],
        rng_seed=d["rng_seed"], last_enemy_move=last_enemy_move, version=d.get("version",1)
    )

def save_state(state: GameState, path="save.json"):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(serialize(state), f, separators=(",", ":"))
    os.replace(tmp, path)

def load_state(path="save.json") -> GameState:
    with open(path, "r", encoding="utf-8") as f:
        return deserialize(json.load(f))
