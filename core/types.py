# core/types.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple, Optional, List, Set, Dict

# Defines types and classes that will be used by other files

Pos = Tuple[int, int]  # (row, col)

# Class CellState can have three values hidden, revealed, or flagged
class CellState(Enum):
    HIDDEN = auto()
    REVEALED = auto()
    FLAGGED = auto()

@dataclass
class Cell:
    state: CellState = CellState.HIDDEN
    has_mine: bool = False
    number: int = 0  # 0..8 (only meaningful if revealed)

class Turn(Enum):
    PLAYER = auto()
    ENEMY = auto()

class Phase(Enum):
    INIT = auto()
    PLAYER_INPUT = auto()
    PLAYER_RESOLVE = auto()
    ENEMY_THINK = auto()
    ENEMY_ACT = auto()
    CHECK_WINLOSE = auto()
    GAME_OVER = auto()

class Outcome(Enum):
    ONGOING = auto()
    PLAYER_WIN = auto()
    ENEMY_WIN = auto()

@dataclass
class Move:
    kind: str           # e.g., "REVEAL"
    pos: Pos
    chosen_p: float = 0.0
    rationale: str = ""

@dataclass
class GameState:
    width: int
    height: int
    grid: List[List[Cell]]
    mines: Set[Pos]
    revealed: Set[Pos]
    flags: Set[Pos]
    enemy_hp: int
    enemy_max_hp: int
    total_mines_target: Optional[int]
    turn: Turn
    phase: Phase
    outcome: Outcome
    rng_seed: int
    version: int = 1
