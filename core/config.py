# core/config.py
BOARD_W = 16
BOARD_H = 16
INITIAL_MINES = 40           # randomized baseline
TOTAL_MINES_TARGET = None    # or an int if you want fixed total mines
DAMAGE_PER_MINE = 1
AI_DIFFICULTY = "medium"     # "easy" | "medium" | "hard"
RNG_SEED_DEFAULT = 1337

# UI-ish but harmless here
TILE_SIZE = 32
MARGIN = 8