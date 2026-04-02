# core/board.py
from __future__ import annotations
from typing import List, Set, Iterable
from core.types import *

class Board:
    DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    _neighbor_cache: dict[tuple[int, int, Pos], tuple[Pos, ...]] = {}

    def is_in_bounds(self, state: GameState, p: Pos) -> bool:
        r,c = p
        return 0 <= r < state.height and 0 <= c < state.width

    def neighbors(self, state: GameState, p: Pos) -> Iterable[Pos]:
        key = (state.height, state.width, p)
        cached = self._neighbor_cache.get(key)
        if cached is None:
            r, c = p
            out: list[Pos] = []
            for dr, dc in self.DIRS:
                q = (r + dr, c + dc)
                if self.is_in_bounds(state, q):
                    out.append(q)
            cached = tuple(out)
            self._neighbor_cache[key] = cached
        for q in cached:
            yield q

    def compute_number_from_mines(self, state: GameState, p: Pos) -> int:
        return sum(n in state.mines for n in self.neighbors(state, p))

    def reveal(self, state: GameState, p: Pos, max_reveals: int | None = None) -> List[Pos]:
        if not self.is_in_bounds(state, p):
            return []
        cell = state.grid[p[0]][p[1]]
        if cell.state == CellState.REVEALED:
            return []
        newly: List[Pos] = []

        def _budget_available() -> bool:
            return max_reveals is None or len(newly) < max_reveals

        def _reveal(q: Pos):
            if not _budget_available():
                return
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
        if not _budget_available():
            return []
        _reveal(p)
        # flood if zero and safe
        if newly and state.grid[p[0]][p[1]].number == 0 and p not in state.mines:
            from collections import deque
            dq = deque([p])
            while dq and _budget_available():
                cur = dq.popleft()
                if state.grid[cur[0]][cur[1]].number != 0: 
                    continue
                for nb in self.neighbors(state, cur):
                    if not _budget_available():
                        break
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
        - p must be in-bounds, unrevealed (HIDDEN or FLAGGED), and not already a mine.
        - (Optional) respect state.total_mines_target if set.
        - We do NOT reveal anything here; just mutate the truth (state.mines) and neighbor numbers.
        """
        # basic checks
        if not self.is_in_bounds(state, p):
            return False

        cell = state.grid[p[0]][p[1]]
        if cell.state == CellState.REVEALED:
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

    def pickup_mine_and_update_numbers(self, state: GameState, p: Pos) -> bool:
        """
        Remove a mine from an unrevealed tile and update numbers on all
        REVEALED, non-mine neighbor tiles (-1 each). Returns True if removed.

        Rules:
        - p must be in-bounds, unrevealed, and currently contain a mine.
        - Does NOT modify mine stock.
        """
        if not self.is_in_bounds(state, p):
            return False

        cell = state.grid[p[0]][p[1]]
        if cell.state == CellState.REVEALED:
            return False
        if p not in state.mines:
            return False

        state.mines.remove(p)

        for nb in self.neighbors(state, p):
            nb_cell = state.grid[nb[0]][nb[1]]
            if nb_cell.state == CellState.REVEALED and nb_cell.number >= 0:
                nb_cell.number -= 1

        return True

    def cover_safe_tile(self, state: GameState, p: Pos) -> bool:
        """
        Cover (re-hide) a revealed non-mine tile so AI may need to uncover it again.
        Returns True if covered.
        """
        if not self.is_in_bounds(state, p):
            return False
        cell = state.grid[p[0]][p[1]]
        if cell.state != CellState.REVEALED:
            return False
        if cell.number < 0 or p in state.mines:
            return False

        cell.state = CellState.HIDDEN
        state.revealed.discard(p)
        return True
