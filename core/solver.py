# core/solver.py
from __future__ import annotations
import random
from typing import Optional, Dict, Set, Tuple
from core.types import GameState, Move, Pos, CellState
from core.board import Board
from core.sweep_board import sweep_frontier

_rng = random.Random(1337)  # seed as you like

def _hidden_neighbors(state: GameState, p: Pos, board: Board) -> list[Pos]:
    return [nb for nb in board.neighbors(state, p)
            if state.grid[nb[0]][nb[1]].state == CellState.HIDDEN]

def _flag_cell(state: GameState, q: Pos) -> None:
    state.flags.add(q)
    cell = state.grid[q[0]][q[1]]
    if cell.state == CellState.HIDDEN:
        cell.state = CellState.FLAGGED

def deduce_and_move_from_sweep(state: GameState) -> Optional[Move]:
    """
    Simple rules:
      - Flag guaranteed mines (remaining == hidden).
      - Collect guaranteed safes (remaining == 0) and reveal one at random.
      - Otherwise compute local p = remaining/hidden for each clue and assign to each
        hidden neighbor, keeping the MINIMUM p seen so far for each tile.
      - Click a random tile among the minimum-p set.
    """
    board = Board()
    info = sweep_frontier(state)

    guaranteed_safe: Set[Pos] = set()
    guaranteed_mines: Set[Pos] = set()

    # Start every tile at p=1.0 (max risk); update with min(local_p)
    prob: Dict[Pos, float] = {}

    for pos, number, hidden, flagged, revealed_mines in info:
        remaining = number - (flagged + revealed_mines)
        if remaining < 0 or remaining > hidden:
            # inconsistent clue; skip defensively
            continue

        hidden_nbs = _hidden_neighbors(state, pos, board)

        # Deductions
        if remaining == 0:
            for q in hidden_nbs:
                guaranteed_safe.add(q)
        elif remaining == hidden:
            for q in hidden_nbs:
                guaranteed_mines.add(q)

        # Local probability for non-deductive cases
        if 0 < remaining < hidden:
            local_p = remaining / hidden
            for q in hidden_nbs:
                if state.grid[q[0]][q[1]].state == CellState.FLAGGED:
                    continue
                # keep the minimum probability encountered for this tile
                prev = prob.get(q, 1.0)
                if local_p < prev:
                    prob[q] = local_p

    # Apply guaranteed flags first
    for q in guaranteed_mines:
        _flag_cell(state, q)

    # Reveal a guaranteed-safe tile if we have any
    safe_list = [q for q in guaranteed_safe if state.grid[q[0]][q[1]].state == CellState.HIDDEN]
    if safe_list:
        choice = _rng.choice(safe_list)
        return Move(kind="REVEAL", pos=choice, chosen_p=0.0, rationale="deduced safe")

    # No certain safe → pick a tile with the lowest p (random tiebreak)
    candidates: list[Tuple[Pos, float]] = [(q, p) for q, p in prob.items() if state.grid[q[0]][q[1]].state == CellState.HIDDEN]

    if candidates:
        min_p = min(p for _, p in candidates)
        best = [q for (q, p) in candidates if abs(p - min_p) < 1e-12] # comparison for floating point error
        choice = _rng.choice(best)
        return Move(kind="REVEAL", pos=choice, chosen_p=min_p, rationale=f"min-risk p≈{min_p:.3f}")

    # If the frontier gave us no probabilities (e.g., no revealed numbers touch hidden tiles),
    # fall back to any hidden tile on the board.
    any_hidden: list[Pos] = []
    for r in range(state.height):
        for c in range(state.width):
            if state.grid[r][c].state == CellState.HIDDEN:
                any_hidden.append((r, c))
    if not any_hidden:
        return None

    choice = _rng.choice(any_hidden)
    return Move(kind="REVEAL", pos=choice, chosen_p=0.5, rationale="fallback (no frontier)")