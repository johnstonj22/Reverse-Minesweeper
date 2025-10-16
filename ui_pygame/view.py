# ui_pygame/view.py
import pygame
from core.types import *
from core.config import TILE_SIZE, MARGIN

COL_BG   = (25, 25, 28)
COL_GRID = (60, 60, 70)
COL_TEXT = (230,230,230)
COL_HP   = (200,60,60)

def draw(screen: pygame.Surface, state: GameState, font: pygame.font.Font):
    screen.fill(COL_BG)

    # board
    ox, oy = MARGIN, 60
    for r in range(state.height):
        for c in range(state.width):
            x = ox + c*TILE_SIZE; y = oy + r*TILE_SIZE
            rect = pygame.Rect(x, y, TILE_SIZE-1, TILE_SIZE-1)
            cell = state.grid[r][c]
            if cell.state == CellState.HIDDEN:
                pygame.draw.rect(screen, COL_GRID, rect)
            else:
                pygame.draw.rect(screen, (100,100,110), rect)
                if cell.number == -1:
                    # mine (revealed)
                    pygame.draw.circle(screen, (220,50,50), rect.center, TILE_SIZE//4)
                elif cell.number > 0:
                    txt = font.render(str(cell.number), True, COL_TEXT)
                    screen.blit(txt, txt.get_rect(center=rect.center))

    # HUD: enemy HP
    hp_text = font.render(f"Enemy HP: {state.enemy_hp}", True, COL_TEXT)
    screen.blit(hp_text, (MARGIN, MARGIN))

    # Phase/Turn
    phase_text = font.render(f"{state.turn.name} / {state.phase.name}", True, COL_TEXT)
    screen.blit(phase_text, (MARGIN + 200, MARGIN))
