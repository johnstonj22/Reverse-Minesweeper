from __future__ import annotations
from core.types import *
from core.board import Board
from core.solver import deduce_and_move_from_sweep
from core.config import (
    DAMAGE_PER_MINE,
    AI_REVEAL_QUOTA,
    PLAYER_MINE_GAIN_PER_TURN,
    PLAYER_RECOVER_GAIN_PER_TURN,
)

_board = Board()


def all_safe_revealed(state: GameState) -> bool:
    total = state.width * state.height
    safe_total = total - len(state.mines)
    safe_revealed = sum(
        1
        for r in range(state.height)
        for c in range(state.width)
        if state.grid[r][c].state == CellState.REVEALED and state.grid[r][c].number >= 0
    )
    return safe_revealed >= safe_total


def step(state: GameState, intent: dict | None = None) -> GameState:
    # --- PLAYER INPUT ---
    if state.phase == Phase.PLAYER_INPUT:
        state.last_enemy_move = None
        if intent and intent.get("type") == "SET_ACTION_MODE":
            mode = intent.get("mode")
            if mode in ("PLACE", "PICKUP", "COVER"):
                state.player_action_mode = mode

        # Player turn ends only when both action stocks are exhausted.
        if state.mine_stock <= 0 and state.recover_stock <= 0:
            state.turn = Turn.ENEMY
            state.ai_reveals_remaining = AI_REVEAL_QUOTA
            state.phase = Phase.ENEMY_THINK
            return state

        def _do_place(pos: Pos):
            if state.mine_stock <= 0:
                return
            placed = _board.place_mine_and_update_numbers(state, pos)
            if placed:
                state.mine_stock -= 1

        def _do_pickup(pos: Pos):
            _board.pickup_mine_and_update_numbers(state, pos)

        def _do_cover(pos: Pos):
            if state.recover_stock <= 0:
                return
            covered = _board.cover_safe_tile(state, pos)
            if covered:
                state.recover_stock -= 1

        if intent and intent.get("type") == "PLACE_MINE":
            _do_place(intent["pos"])
        elif intent and intent.get("type") == "PICKUP_MINE":
            _do_pickup(intent["pos"])
        elif intent and intent.get("type") == "COVER_TILE":
            _do_cover(intent["pos"])
        elif intent and intent.get("type") == "PLACE_MINE_BATCH":
            for pos in intent.get("positions", []):
                if state.mine_stock <= 0 and state.recover_stock <= 0:
                    break
                _do_place(pos)
        elif intent and intent.get("type") == "PICKUP_MINE_BATCH":
            for pos in intent.get("positions", []):
                _do_pickup(pos)
        elif intent and intent.get("type") == "COVER_TILE_BATCH":
            for pos in intent.get("positions", []):
                if state.mine_stock <= 0 and state.recover_stock <= 0:
                    break
                _do_cover(pos)
        elif intent and intent.get("type") == "SKIP_TURN":
            state.turn = Turn.ENEMY
            state.ai_reveals_remaining = AI_REVEAL_QUOTA
            state.phase = Phase.ENEMY_THINK
            return state

        if state.mine_stock <= 0 and state.recover_stock <= 0:
            state.turn = Turn.ENEMY
            state.ai_reveals_remaining = AI_REVEAL_QUOTA
            state.phase = Phase.ENEMY_THINK
        else:
            state.turn = Turn.PLAYER
            state.phase = Phase.PLAYER_INPUT
        return state

    # --- ENEMY THINK ---
    if state.phase == Phase.ENEMY_THINK:
        if state.ai_reveals_remaining <= 0:
            state.phase = Phase.CHECK_WINLOSE
            return state

        move = deduce_and_move_from_sweep(state)
        state.last_enemy_move = move
        if move is None:
            state.ai_reveals_remaining = 0
            state.phase = Phase.CHECK_WINLOSE
            return state

        newly = _board.reveal(state, move.pos, max_reveals=state.ai_reveals_remaining)
        if not newly:
            state.ai_reveals_remaining = 0
            state.phase = Phase.CHECK_WINLOSE
            return state

        state.ai_reveals_remaining -= len(newly)
        if move.pos in state.mines:
            state.enemy_hp -= DAMAGE_PER_MINE

        if state.ai_reveals_remaining <= 0:
            state.phase = Phase.CHECK_WINLOSE
        else:
            state.phase = Phase.ENEMY_THINK
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
            state.mine_stock += PLAYER_MINE_GAIN_PER_TURN
            state.recover_stock += PLAYER_RECOVER_GAIN_PER_TURN
            state.ai_reveals_remaining = 0
            state.turn = Turn.PLAYER
            state.phase = Phase.PLAYER_INPUT
        return state

    return state
