# ui_pygame/view.py
import pygame
from core.types import *
from core.config import TILE_SIZE, MARGIN

COL_BG   = (25, 25, 28)
COL_GRID = (60, 60, 70)
COL_TEXT = (230,230,230)
COL_HP   = (200,60,60)
COL_MINE_FADED = (130, 70, 70)
COL_MINE_HIT = (220, 50, 50)
COL_FLAG = (255, 200, 90)
COL_BTN = (85, 95, 120)
COL_BTN_TEXT = (245, 245, 245)
COL_BTN_ACTIVE = (120, 135, 170)

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
                # Show player-placed mines as faded markers until the AI reveals them.
                if (r, c) in state.mines:
                    pygame.draw.circle(screen, COL_MINE_FADED, rect.center, TILE_SIZE//5)
            elif cell.state == CellState.FLAGGED:
                pygame.draw.rect(screen, COL_GRID, rect)
                # If a mine exists under a flag, keep it subtle until AI reveals it.
                if (r, c) in state.mines:
                    pygame.draw.circle(screen, COL_MINE_FADED, rect.center, TILE_SIZE//6)
                # AI-marked flag so deductions are visible to the player.
                pole_x = rect.left + TILE_SIZE // 3
                pole_top = rect.top + TILE_SIZE // 5
                pole_bottom = rect.bottom - TILE_SIZE // 5
                pygame.draw.line(screen, COL_TEXT, (pole_x, pole_top), (pole_x, pole_bottom), 2)
                flag_pts = [
                    (pole_x, pole_top),
                    (pole_x + TILE_SIZE // 3, pole_top + TILE_SIZE // 7),
                    (pole_x, pole_top + TILE_SIZE // 3),
                ]
                pygame.draw.polygon(screen, COL_FLAG, flag_pts)
            else:
                pygame.draw.rect(screen, (100,100,110), rect)
                if cell.number == -1:
                    # Mine hit/revealed by AI.
                    pygame.draw.circle(screen, COL_MINE_HIT, rect.center, TILE_SIZE//4)
                elif cell.number > 0:
                    txt = font.render(str(cell.number), True, COL_TEXT)
                    screen.blit(txt, txt.get_rect(center=rect.center))

    # HUD: enemy HP
    hp_text = font.render(f"Enemy HP: {state.enemy_hp}", True, COL_TEXT)
    screen.blit(hp_text, (MARGIN, MARGIN))

    stock_text = font.render(f"Mine Stock: {state.mine_stock}", True, COL_TEXT)
    screen.blit(stock_text, (MARGIN + 130, MARGIN))

    # Phase/Turn
    phase_text = font.render(f"{state.turn.name} / {state.phase.name}", True, COL_TEXT)
    screen.blit(phase_text, (MARGIN + 310, MARGIN))

    # Player action mode controls.
    if state.phase == Phase.PLAYER_INPUT:
        place_rect = pygame.Rect(MARGIN + 500, MARGIN - 2, 90, 28)
        pickup_rect = pygame.Rect(MARGIN + 600, MARGIN - 2, 90, 28)
        place_col = COL_BTN_ACTIVE if state.player_action_mode == "PLACE" else COL_BTN
        pickup_col = COL_BTN_ACTIVE if state.player_action_mode == "PICKUP" else COL_BTN
        pygame.draw.rect(screen, place_col, place_rect, border_radius=4)
        pygame.draw.rect(screen, pickup_col, pickup_rect, border_radius=4)
        place_label = font.render("Place", True, COL_BTN_TEXT)
        pickup_label = font.render("Pickup", True, COL_BTN_TEXT)
        screen.blit(place_label, place_label.get_rect(center=place_rect.center))
        screen.blit(pickup_label, pickup_label.get_rect(center=pickup_rect.center))

    # Skip turn control (only useful when player can still act).
    if state.phase == Phase.PLAYER_INPUT and state.mine_stock > 0:
        btn_rect = pygame.Rect(MARGIN + 700, MARGIN - 2, 120, 28)
        pygame.draw.rect(screen, COL_BTN, btn_rect, border_radius=4)
        label = font.render("Skip Turn", True, COL_BTN_TEXT)
        screen.blit(label, label.get_rect(center=btn_rect.center))

    # Show AI "thinking" feedback during the intentional delay.
    if state.phase == Phase.ENEMY_THINK:
        dots = "." * ((pygame.time.get_ticks() // 300) % 4)
        think_text = font.render(f"AI thinking{dots}", True, COL_TEXT)
        screen.blit(think_text, (MARGIN + 460, MARGIN))
