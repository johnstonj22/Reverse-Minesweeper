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
COL_PANEL = (34, 38, 48)
COL_LOG_ROW = (60, 66, 82)
COL_LOG_ACTIVE = (85, 120, 100)
COL_LOG_LATEST = (80, 86, 105)
COL_LOG_DETAIL = (45, 50, 64)
COL_LOG_TITLE = (188, 198, 222)

def _wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        if font.size(trial)[0] <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines

def draw(
    screen: pygame.Surface,
    state: GameState,
    font: pygame.font.Font,
    move_log: list[dict] | None = None,
    active_log_index: int | None = None,
    log_scroll_start: int = 0,
):
    if move_log is None:
        move_log = []
    if active_log_index is None:
        active_log_index = len(move_log) - 1

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
    recover_text = font.render(f"Recover Stock: {state.recover_stock}", True, COL_TEXT)
    screen.blit(recover_text, (MARGIN + 280, MARGIN))

    # Phase/Turn
    phase_text = font.render(f"{state.turn.name} / {state.phase.name}", True, COL_TEXT)
    screen.blit(phase_text, (MARGIN + 470, MARGIN))

    # Player action mode controls.
    if state.phase == Phase.PLAYER_INPUT:
        place_rect = pygame.Rect(MARGIN + 470, MARGIN - 2, 90, 28)
        pickup_rect = pygame.Rect(MARGIN + 560, MARGIN - 2, 90, 28)
        cover_rect = pygame.Rect(MARGIN + 650, MARGIN - 2, 90, 28)
        place_col = COL_BTN_ACTIVE if state.player_action_mode == "PLACE" else COL_BTN
        pickup_col = COL_BTN_ACTIVE if state.player_action_mode == "PICKUP" else COL_BTN
        cover_col = COL_BTN_ACTIVE if state.player_action_mode == "COVER" else COL_BTN
        pygame.draw.rect(screen, place_col, place_rect, border_radius=4)
        pygame.draw.rect(screen, pickup_col, pickup_rect, border_radius=4)
        pygame.draw.rect(screen, cover_col, cover_rect, border_radius=4)
        place_label = font.render("Place", True, COL_BTN_TEXT)
        pickup_label = font.render("Pickup", True, COL_BTN_TEXT)
        cover_label = font.render("Cover", True, COL_BTN_TEXT)
        screen.blit(place_label, place_label.get_rect(center=place_rect.center))
        screen.blit(pickup_label, pickup_label.get_rect(center=pickup_rect.center))
        screen.blit(cover_label, cover_label.get_rect(center=cover_rect.center))

    # Skip turn control.
    if state.phase == Phase.PLAYER_INPUT:
        btn_rect = pygame.Rect(MARGIN + 740, MARGIN - 2, 120, 28)
        pygame.draw.rect(screen, COL_BTN, btn_rect, border_radius=4)
        label = font.render("Skip Turn", True, COL_BTN_TEXT)
        screen.blit(label, label.get_rect(center=btn_rect.center))

    # Show AI "thinking" feedback during the intentional delay.
    if state.phase == Phase.ENEMY_THINK:
        dots = "." * ((pygame.time.get_ticks() // 300) % 4)
        think_text = font.render(f"AI thinking{dots}", True, COL_TEXT)
        screen.blit(think_text, (MARGIN + 460, MARGIN))

    # Move log panel
    hitboxes: list[tuple[int, pygame.Rect]] = []
    panel_x = MARGIN + state.width * TILE_SIZE + 24
    panel_y = 60
    panel_w = screen.get_width() - panel_x - MARGIN
    panel_h = screen.get_height() - panel_y - MARGIN
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(screen, COL_PANEL, panel_rect, border_radius=6)

    title = font.render("Move Log (click to jump)", True, COL_TEXT)
    screen.blit(title, (panel_x + 10, panel_y + 8))

    detail_h = 128
    list_h = panel_h - 40 - detail_h - 8
    row_h = 24
    max_rows = max(1, list_h // row_h)
    max_start = max(0, len(move_log) - max_rows)
    start_idx = max(0, min(log_scroll_start, max_start))

    for row, idx in enumerate(range(start_idx, len(move_log))):
        if row >= max_rows:
            break
        row_rect = pygame.Rect(panel_x + 8, panel_y + 34 + row * row_h, panel_w - 16, row_h - 2)
        if idx == active_log_index:
            bg = COL_LOG_ACTIVE
        elif idx == len(move_log) - 1:
            bg = COL_LOG_LATEST
        else:
            bg = COL_LOG_ROW
        pygame.draw.rect(screen, bg, row_rect, border_radius=4)

        label = move_log[idx].get("label", "")
        txt = font.render(f"{idx:03d}  {label}", True, COL_TEXT)
        screen.blit(txt, (row_rect.x + 6, row_rect.y + 3))
        hitboxes.append((idx, row_rect))

    # Detail box for selected entry
    detail_rect = pygame.Rect(panel_x + 8, panel_y + panel_h - detail_h - 8, panel_w - 16, detail_h)
    pygame.draw.rect(screen, COL_LOG_DETAIL, detail_rect, border_radius=5)
    if 0 <= active_log_index < len(move_log):
        entry = move_log[active_log_index]
        detail_title = font.render(f"Entry {active_log_index:03d}", True, COL_LOG_TITLE)
        screen.blit(detail_title, (detail_rect.x + 8, detail_rect.y + 6))
        details = entry.get("detail", "") or "No extra details."
        lines = _wrap_text(font, details, detail_rect.w - 16)
        max_detail_lines = max(1, (detail_rect.h - 28) // 20)
        for i, line in enumerate(lines[:max_detail_lines]):
            line_surf = font.render(line, True, COL_TEXT)
            screen.blit(line_surf, (detail_rect.x + 8, detail_rect.y + 28 + i * 20))

    if active_log_index != len(move_log) - 1:
        review = font.render("Review mode: click latest log to resume", True, COL_TEXT)
        screen.blit(review, (panel_x + 10, panel_y + panel_h - 26))

    return hitboxes, panel_rect, start_idx, max_start
