from __future__ import annotations
from collections import OrderedDict
from copy import deepcopy
import random
from typing import Optional, Set

from core.board import Board
from core.solver import deduce_and_move_from_sweep
from core.types import GameState, Pos, CellState


_board = Board()
_SAFE_CACHE_MAX = 4096
_safe_cache: "OrderedDict[tuple, Set[Pos]]" = OrderedDict()


def _hidden_neighbors(state: GameState, p: Pos) -> list[Pos]:
    return [nb for nb in _board.neighbors(state, p) if state.grid[nb[0]][nb[1]].state == CellState.HIDDEN]


def _flagged_neighbors(state: GameState, p: Pos) -> list[Pos]:
    return [nb for nb in _board.neighbors(state, p) if state.grid[nb[0]][nb[1]].state == CellState.FLAGGED]


def _revealed_mine_neighbors(state: GameState, p: Pos) -> int:
    return sum(
        1
        for nb in _board.neighbors(state, p)
        if state.grid[nb[0]][nb[1]].state == CellState.REVEALED and state.grid[nb[0]][nb[1]].number == -1
    )


def _state_fingerprint_for_safe_cache(state: GameState) -> tuple:
    revealed_num_tiles: list[tuple[int, int, int]] = []
    for p in state.revealed:
        cell = state.grid[p[0]][p[1]]
        if cell.number >= 0:
            revealed_num_tiles.append((p[0], p[1], cell.number))
    revealed_num_tiles.sort()

    return (
        state.width,
        state.height,
        tuple(sorted(state.mines)),
        tuple(sorted(state.revealed)),
        tuple(sorted(state.flags)),
        tuple(revealed_num_tiles),
    )


def _enemy_safe_tiles(state: GameState) -> Set[Pos]:
    """
    Compute hidden tiles currently deducible as safe under enemy logic.
    Uses a clone and runs enemy deduction once to sync provisional flags first.
    Memoized by board fingerprint to accelerate batch sims.
    """
    key = _state_fingerprint_for_safe_cache(state)
    cached = _safe_cache.get(key)
    if cached is not None:
        _safe_cache.move_to_end(key)
        return set(cached)

    shadow = deepcopy(state)
    deduce_and_move_from_sweep(shadow)

    safe: Set[Pos] = set()
    for r in range(shadow.height):
        for c in range(shadow.width):
            clue = shadow.grid[r][c]
            if clue.state != CellState.REVEALED or clue.number < 0:
                continue
            p = (r, c)
            hidden_nbs = _hidden_neighbors(shadow, p)
            if not hidden_nbs:
                continue
            known_mines = len(_flagged_neighbors(shadow, p)) + _revealed_mine_neighbors(shadow, p)
            if clue.number - known_mines == 0:
                safe.update(hidden_nbs)

    _safe_cache[key] = set(safe)
    if len(_safe_cache) > _SAFE_CACHE_MAX:
        _safe_cache.popitem(last=False)
    return safe


def _cover_candidates_for_target(state: GameState, t: Pos, limit: int) -> list[Pos]:
    # Cover revealed safe clues near target first, then 2-hop clues.
    candidates: list[Pos] = []
    seen: set[Pos] = set()
    ring: list[Pos] = [t]
    for _ in range(2):
        next_ring: list[Pos] = []
        for p in ring:
            for nb in _board.neighbors(state, p):
                if nb in seen:
                    continue
                seen.add(nb)
                next_ring.append(nb)
                cell = state.grid[nb[0]][nb[1]]
                if cell.state == CellState.REVEALED and cell.number >= 0 and nb not in state.mines:
                    candidates.append(nb)
                if len(candidates) >= limit:
                    return candidates[:limit]
        ring = next_ring
    return candidates[:limit]


def _place_candidates_for_target(state: GameState, t: Pos, limit: int) -> list[Pos]:
    candidates: list[Pos] = []
    candidates.append(t)
    for nb in _board.neighbors(state, t):
        if nb not in candidates:
            candidates.append(nb)
        if len(candidates) >= limit:
            return candidates[:limit]
    return candidates[:limit]


def _pickup_candidates_for_target(state: GameState, t: Pos, limit: int) -> list[Pos]:
    candidates: list[Pos] = []
    candidates.append(t)
    for nb in _board.neighbors(state, t):
        if nb not in candidates:
            candidates.append(nb)
        if len(candidates) >= limit:
            return candidates[:limit]

    local: set[Pos] = set(candidates)
    for p in list(local):
        for nb in _board.neighbors(state, p):
            local.add(nb)
    for p in local:
        if p in state.mines and p not in candidates:
            candidates.append(p)
        if len(candidates) >= limit:
            return candidates[:limit]
    return candidates[:limit]


def _budget_spent(counter_probe_count: list[int], counter_probe_budget: int) -> bool:
    return counter_probe_count[0] >= counter_probe_budget


def _try_cover_counter(state: GameState, target: Pos, counter_probe_count: list[int], counter_probe_budget: int, fast_mode: bool) -> Optional[dict]:
    if state.recover_stock <= 0 or _budget_spent(counter_probe_count, counter_probe_budget):
        return None
    cover_limit = 3 if fast_mode else 6
    for p in _cover_candidates_for_target(state, target, cover_limit):
        if _budget_spent(counter_probe_count, counter_probe_budget):
            return None
        counter_probe_count[0] += 1
        test = deepcopy(state)
        if not _board.cover_safe_tile(test, p):
            continue
        safe_after = _enemy_safe_tiles(test)
        if target not in safe_after:
            return {"type": "COVER_TILE", "pos": p}
    return None


def _try_place_counter(state: GameState, target: Pos, counter_probe_count: list[int], counter_probe_budget: int, fast_mode: bool) -> Optional[dict]:
    if state.mine_stock <= 0 or _budget_spent(counter_probe_count, counter_probe_budget):
        return None
    place_limit = 2 if fast_mode else 4
    for p in _place_candidates_for_target(state, target, place_limit):
        if _budget_spent(counter_probe_count, counter_probe_budget):
            return None
        counter_probe_count[0] += 1
        test = deepcopy(state)
        if not _board.place_mine_and_update_numbers(test, p):
            continue
        safe_after = _enemy_safe_tiles(test)
        if target not in safe_after:
            return {"type": "PLACE_MINE", "pos": p}
    return None


def _try_pickup_counter(state: GameState, target: Pos, counter_probe_count: list[int], counter_probe_budget: int, fast_mode: bool) -> Optional[dict]:
    if fast_mode or _budget_spent(counter_probe_count, counter_probe_budget):
        return None
    pickup_limit = 6
    for p in _pickup_candidates_for_target(state, target, pickup_limit):
        if _budget_spent(counter_probe_count, counter_probe_budget):
            return None
        counter_probe_count[0] += 1
        test = deepcopy(state)
        if not _board.pickup_mine_and_update_numbers(test, p):
            continue
        safe_after = _enemy_safe_tiles(test)
        if target not in safe_after:
            return {"type": "PICKUP_MINE", "pos": p}
    return None


def _rng_for_state(state: GameState) -> random.Random:
    seed = (
        state.rng_seed
        + 97 * len(state.revealed)
        + 131 * len(state.mines)
        + 17 * state.mine_stock
        + 19 * state.recover_stock
    )
    return random.Random(seed)


def _frontier_unrevealed_tiles(state: GameState) -> list[Pos]:
    frontier: set[Pos] = set()
    for p in state.revealed:
        cell = state.grid[p[0]][p[1]]
        if cell.number < 0:
            continue
        for nb in _board.neighbors(state, p):
            if state.grid[nb[0]][nb[1]].state != CellState.REVEALED:
                frontier.add(nb)
    return sorted(frontier)


def _random_place_intent(state: GameState, rng: random.Random) -> Optional[dict]:
    if state.mine_stock <= 0:
        return None
    frontier = [p for p in _frontier_unrevealed_tiles(state) if p not in state.mines]
    if frontier:
        return {"type": "PLACE_MINE", "pos": rng.choice(frontier)}

    candidates: list[Pos] = []
    for r in range(state.height):
        for c in range(state.width):
            p = (r, c)
            cell = state.grid[r][c]
            if cell.state != CellState.REVEALED and p not in state.mines:
                candidates.append(p)
    if not candidates:
        return None
    return {"type": "PLACE_MINE", "pos": rng.choice(candidates)}


def _random_cover_intent(state: GameState, rng: random.Random) -> Optional[dict]:
    if state.recover_stock <= 0:
        return None
    candidates: list[Pos] = []
    for p in state.revealed:
        cell = state.grid[p[0]][p[1]]
        if cell.number >= 0 and p not in state.mines:
            candidates.append(p)
    if not candidates:
        return None
    return {"type": "COVER_TILE", "pos": rng.choice(candidates)}


def choose_player_intent(state: GameState, fast_mode: bool = False, counter_probe_budget: int = 24) -> dict:
    """
    Counter-safe-first policy:
    - Find currently deducible enemy-safe hidden tiles.
    - For each safe tile, try to invalidate it in this order: COVER -> PLACE -> PICKUP.
    - If none can invalidate a safe tile, mark it uncounterable and continue.
    - When no safe tiles remain, use random disrupt (random PLACE/COVER) until stocks run out.

    Optimizations for batch simulation:
    - memoized enemy-safe analysis
    - bounded candidate lists
    - bounded counter-probe budget
    - optional fast mode (skips pickup-counter branch)
    """
    uncounterable: Set[Pos] = set()
    counter_probe_count = [0]

    while not _budget_spent(counter_probe_count, counter_probe_budget):
        safe_tiles = _enemy_safe_tiles(state)
        targets = [t for t in safe_tiles if t not in uncounterable]
        if not targets:
            break

        targets.sort()
        target = targets[0]

        intent = _try_cover_counter(state, target, counter_probe_count, counter_probe_budget, fast_mode)
        if intent is not None:
            return intent

        intent = _try_place_counter(state, target, counter_probe_count, counter_probe_budget, fast_mode)
        if intent is not None:
            return intent

        intent = _try_pickup_counter(state, target, counter_probe_count, counter_probe_budget, fast_mode)
        if intent is not None:
            return intent

        uncounterable.add(target)

    rng = _rng_for_state(state)
    intent = _random_place_intent(state, rng)
    if intent is not None:
        return intent

    intent = _random_cover_intent(state, rng)
    if intent is not None:
        return intent

    return {"type": "SKIP_TURN"}
