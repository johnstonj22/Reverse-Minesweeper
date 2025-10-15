# core/board.py
from __future__ import annotations
from typing import List, Set, Iterable
from core.types import *

class Board:
    DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

    def is_in_bounds(self, state: GameState, p: Pos) -> bool:
        r,c = p
        return 0 <= r < state.height and 0 <= c < state.width

    def neighbors(self, state: GameState, p: Pos) -> Iterable[Pos]:
        r,c = p
        for dr,dc in self.DIRS:
            q = (r+dr, c+dc)
            if self.is_in_bounds(state, q):
                yield q

    def compute_number_from_mines(self, state: GameState, p: Pos) -> int:
        return sum(n in state.mines for n in self.neighbors(state, p))

    def reveal(self, state: GameState, p: Pos) -> List[Pos]:
        if not self.is_in_bounds(state, p):
            return []
        cell = state.grid[p[0]][p[1]]
        if cell.state == CellState.REVEALED:
            return []
        newly: List[Pos] = []
        def _reveal(q: Pos):
            cq = state.grid[q[0]][q[1]]
            if cq.state != CellState.HIDDEN:
                return
            cq.state = CellState.REVEALED
            state.revealed.add(q)
            if q in state.mines:
                cq.has_mine = True
                cq.number = -1
            else:
                cq.has_mine = False
                cq.number = self.compute_number_from_mines(state, q)
            newly.append(q)

        # click
        _reveal(p)
        # flood if zero and safe
        if state.grid[p[0]][p[1]].number == 0 and p not in state.mines:
            from collections import deque
            dq = deque([p])
            while dq:
                cur = dq.popleft()
                if state.grid[cur[0]][cur[1]].number != 0: 
                    continue
                for nb in self.neighbors(state, cur):
                    if state.grid[nb[0]][nb[1]].state == CellState.HIDDEN and nb not in state.mines:
                        _reveal(nb)
                        if state.grid[nb[0]][nb[1]].number == 0:
                            dq.append(nb)
        return newly

    def place_mine_raw(self, state: GameState, p: Pos) -> None:
        # Use only after legality check
        state.mines.add(p)

    def place_mine_and_update_numbers(self, state: GameState, p: Pos) -> bool:
        """
        Place a mine on any HIDDEN tile p and update numbers on all
        REVEALED, non-mine neighbor tiles (+1 each). Returns True if placed, False otherwise.

        Rules:
        - p must be in-bounds, HIDDEN, and not already a mine.
        - (Optional) respect state.total_mines_target if set.
        - We do NOT reveal anything here; just mutate the truth (state.mines) and neighbor numbers.
        """
        # basic checks
        if not self.is_in_bounds(state, p):
            return False

        cell = state.grid[p[0]][p[1]]
        if cell.state != CellState.HIDDEN:
            return False
        if p in state.mines:
            return False

        # optional mine budget
        if state.total_mines_target is not None:
            if len(state.mines) + 1 > state.total_mines_target:
                return False

        # add the mine to truth set
        state.mines.add(p)

        # update numbers for any REVEALED, non-mine neighbor cells
        for nb in self.neighbors(state, p):
            nb_cell = state.grid[nb[0]][nb[1]]

            # Only adjust visible number clues
            if nb_cell.state == CellState.REVEALED:
                if nb_cell.number >= 0:
                    nb_cell.number += 1
                # if nb_cell.number == -1 → it's a revealed mine; leave as-is
            # HIDDEN or FLAGGED neighbors hold no visible number → nothing to change now

        return True