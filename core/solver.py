# core/solver.py
from __future__ import annotations
import random
from typing import Optional, Dict, Set, Tuple
from core.types import GameState, Move, Pos, CellState
from core.board import Board

_rng = random.Random(1337)  # seed as you like


def _hidden_neighbors(state: GameState, p: Pos, board: Board) -> list[Pos]:
    return [nb for nb in board.neighbors(state, p)
            if state.grid[nb[0]][nb[1]].state == CellState.HIDDEN]


def _unrevealed_neighbors(state: GameState, p: Pos, board: Board) -> list[Pos]:
    return [nb for nb in board.neighbors(state, p)
            if state.grid[nb[0]][nb[1]].state != CellState.REVEALED]


def _flagged_neighbors(state: GameState, p: Pos, board: Board) -> list[Pos]:
    return [nb for nb in board.neighbors(state, p)
            if state.grid[nb[0]][nb[1]].state == CellState.FLAGGED]


def _revealed_mine_neighbors(state: GameState, p: Pos, board: Board) -> int:
    n = 0
    for nb in board.neighbors(state, p):
        nb_cell = state.grid[nb[0]][nb[1]]
        if nb_cell.state == CellState.REVEALED and nb_cell.number == -1:
            n += 1
    return n


def _flag_cell(state: GameState, q: Pos) -> None:
    state.flags.add(q)
    cell = state.grid[q[0]][q[1]]
    if cell.state == CellState.HIDDEN:
        cell.state = CellState.FLAGGED


def _unflag_cell(state: GameState, q: Pos) -> None:
    state.flags.discard(q)
    cell = state.grid[q[0]][q[1]]
    if cell.state == CellState.FLAGGED:
        cell.state = CellState.HIDDEN


def _deduce_guaranteed_mines(state: GameState, board: Board) -> Set[Pos]:
    """
    Derive guaranteed-mine tiles from revealed clues only, without trusting current flags.
    """
    deduced: Set[Pos] = set()
    changed = True
    while changed:
        changed = False
        for r in range(state.height):
            for c in range(state.width):
                clue = state.grid[r][c]
                if clue.state != CellState.REVEALED or clue.number < 0:
                    continue

                p = (r, c)
                unrevealed = _unrevealed_neighbors(state, p, board)
                if not unrevealed:
                    continue

                already_deduced = [q for q in unrevealed if q in deduced]
                unknown = [q for q in unrevealed if q not in deduced]
                known_mines = len(already_deduced) + _revealed_mine_neighbors(state, p, board)
                remaining = clue.number - known_mines

                if remaining < 0:
                    continue
                if remaining == len(unknown) and unknown:
                    for q in unknown:
                        if q not in deduced:
                            deduced.add(q)
                            changed = True
    return deduced


def deduce_and_move_from_sweep(state: GameState) -> Optional[Move]:
    """
    Enemy-turn solve flow:
      1) Scan all revealed-number clues and repeatedly FLAG guaranteed mines.
      2) Treat flags as known mines, then collect guaranteed-safe hidden cells.
      3) If no guaranteed safe, use local min-risk probability over hidden cells.
    """
    board = Board()

    # Pass 0: validate existing flags, then apply freshly deduced flags.
    deduced_mines = _deduce_guaranteed_mines(state, board)

    # Remove any stale flags first.
    current_flagged: list[Pos] = []
    for r in range(state.height):
        for c in range(state.width):
            if state.grid[r][c].state == CellState.FLAGGED:
                current_flagged.append((r, c))
    for q in current_flagged:
        if q not in deduced_mines:
            _unflag_cell(state, q)

    # Apply all currently deducible mine flags.
    for q in deduced_mines:
        _flag_cell(state, q)

    # Pass 2: treat flags as known mines and collect guaranteed-safe hidden cells.
    guaranteed_safe: Set[Pos] = set()
    for r in range(state.height):
        for c in range(state.width):
            clue = state.grid[r][c]
            if clue.state != CellState.REVEALED or clue.number < 0:
                continue

            p = (r, c)
            hidden_nbs = _hidden_neighbors(state, p, board)
            if not hidden_nbs:
                continue

            flagged_nbs = _flagged_neighbors(state, p, board)
            known_mines = len(flagged_nbs) + _revealed_mine_neighbors(state, p, board)
            remaining = clue.number - known_mines
            if remaining < 0:
                continue
            if remaining == 0:
                guaranteed_safe.update(hidden_nbs)

    if guaranteed_safe:
        choice = _rng.choice(list(guaranteed_safe))
        return Move(kind="REVEAL", pos=choice, chosen_p=0.0, rationale="deduced safe")

    # Pass 3: local probability over hidden neighbors, treating flags as known mines.
    prob: Dict[Pos, float] = {}
    for r in range(state.height):
        for c in range(state.width):
            clue = state.grid[r][c]
            if clue.state != CellState.REVEALED or clue.number < 0:
                continue

            p = (r, c)
            hidden_nbs = _hidden_neighbors(state, p, board)
            if not hidden_nbs:
                continue

            flagged_nbs = _flagged_neighbors(state, p, board)
            known_mines = len(flagged_nbs) + _revealed_mine_neighbors(state, p, board)
            remaining = clue.number - known_mines
            if remaining < 0:
                continue
            if not (0 < remaining < len(hidden_nbs)):
                continue

            local_p = remaining / len(hidden_nbs)
            for q in hidden_nbs:
                prev = prob.get(q, 1.0)
                if local_p < prev:
                    prob[q] = local_p

    candidates: list[Tuple[Pos, float]] = [
        (q, p) for q, p in prob.items() if state.grid[q[0]][q[1]].state == CellState.HIDDEN
    ]
    if candidates:
        min_p = min(p for _, p in candidates)
        best = [q for (q, p) in candidates if abs(p - min_p) < 1e-12]
        choice = _rng.choice(best)
        return Move(kind="REVEAL", pos=choice, chosen_p=min_p, rationale=f"min-risk p~{min_p:.3f}")

    # Fallback: no frontier probabilities, choose any hidden non-flagged tile.
    any_hidden: list[Pos] = []
    for r in range(state.height):
        for c in range(state.width):
            if state.grid[r][c].state == CellState.HIDDEN:
                any_hidden.append((r, c))
    if not any_hidden:
        return None

    choice = _rng.choice(any_hidden)
    return Move(kind="REVEAL", pos=choice, chosen_p=0.5, rationale="fallback (no frontier)")
