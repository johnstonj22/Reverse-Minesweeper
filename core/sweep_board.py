# core/sweep_board.py
from __future__ import annotations
from typing import List, Tuple
from core.types import GameState, Pos, CellState
from core.board import Board

SweepInfo = Tuple[Pos, int, int, int, int]
# (cell_pos, number, hidden_count, flagged_count, revealed_mines_count)

def sweep_frontier(state: GameState) -> List[SweepInfo]:
    board = Board()
    out: List[SweepInfo] = []

    for r in range(state.height):
        for c in range(state.width):
            p = (r, c)
            cell = state.grid[r][c]

            # consider only revealed number tiles (skip revealed mines and hidden)
            if cell.state != CellState.REVEALED or cell.number < 0:
                continue

            hidden = 0
            flagged = 0
            revealed_mines = 0

            for nb in board.neighbors(state, p):
                nb_cell = state.grid[nb[0]][nb[1]]

                if nb_cell.state == CellState.HIDDEN:
                    hidden += 1
                    # (We treat "flags" separately; if you maintain state.flags,
                    #  you can count them here instead of by CellState.)
                    if nb in state.flags:
                        flagged += 1
                elif nb_cell.state == CellState.FLAGGED:
                    flagged += 1
                elif nb_cell.state == CellState.REVEALED and nb_cell.number == -1:
                    revealed_mines += 1

            if hidden > 0:
                out.append((p, cell.number, hidden, flagged, revealed_mines))
    return out