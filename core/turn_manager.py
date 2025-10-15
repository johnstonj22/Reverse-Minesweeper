from __future__ import annotations
from core.types import *
from core.board import Board
from core.solver import deduce_and_move_from_sweep
from core.config import DAMAGE_PER_MINE

_board = Board()

def all_safe_revealed(state: GameState) -> bool:
    total = state.width * state.height
    safe_total = total - len(state.mines)
    safe_revealed = sum(1 for r in range(state.height) for c in range(state.width) if state.grid[r][c].state == CellState.REVEALED and state.grid[r][c].number >= 0)
    return safe_revealed >= safe_total


def step(state: GameState, intent: dict | None = None) -> GameState:
    # --- PLAYER INPUT ---
    if state.phase == Phase.PLAYER_INPUT:
        if intent and intent.get("type") == "PLACE_MINE":
            pos = intent["pos"]
            placed = _board.place_mine_and_update_numbers(state, pos)
            # move to enemy turn only if placement succeeded
            state.phase = Phase.ENEMY_THINK if placed else Phase.PLAYER_INPUT
        return state

    # --- ENEMY THINK ---
    if state.phase == Phase.ENEMY_THINK:
        move = deduce_and_move_from_sweep(state)
        # move may be None if no hidden tiles left
        if move is not None:
            # immediately apply it (we don’t need a separate ACT phase anymore)
            pos = move.pos
            newly = _board.reveal(state, pos)
            if pos in state.mines:
                state.enemy_hp -= DAMAGE_PER_MINE
        state.phase = Phase.CHECK_WINLOSE
        return state

    # --- CHECK WIN/LOSE ---
    if state.phase == Phase.CHECK_WINLOSE:
        if state.enemy_hp <= 0:
            state.outcome = Outcome.PLAYER_WIN
            state.phase = Phase.GAME_OVER
        elif all_safe_revealed(state):
            state.outcome = Outcome.ENEMY_WIN
            state.phase = Phase.GAME_OVER
        else:
            # Next turn: back to player
            state.turn = Turn.PLAYER
            state.phase = Phase.PLAYER_INPUT
        return state

    return state
