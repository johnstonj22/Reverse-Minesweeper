# core/generator.py
import random
from core.types import *
from core.config import *

def new_game(seed: int | None = None) -> GameState:
    if seed is None: seed = RNG_SEED_DEFAULT
    rng = random.Random(seed)
    # baseline mines
    cells = [(r,c) for r in range(BOARD_H) for c in range(BOARD_W)]
    mines = set(rng.sample(cells, INITIAL_MINES))
    # grid
    grid = [[Cell() for _ in range(BOARD_W)] for _ in range(BOARD_H)]
    return GameState(
        width=BOARD_W, height=BOARD_H,
        grid=grid, mines=mines, revealed=set(), flags=set(),
        enemy_hp=3, enemy_max_hp=3,
        total_mines_target=TOTAL_MINES_TARGET,
        turn=Turn.PLAYER, phase=Phase.PLAYER_INPUT, outcome=Outcome.ONGOING,
        rng_seed=seed
    )
