# ui_pygame/input.py
import pygame
from core.types import *
from core.config import MARGIN, TILE_SIZE

SKIP_BTN_X = MARGIN + 740
SKIP_BTN_Y = MARGIN - 2
SKIP_BTN_W = 120
SKIP_BTN_H = 28
PLACE_BTN_X = MARGIN + 470
PICKUP_BTN_X = MARGIN + 560
COVER_BTN_X = MARGIN + 650
MODE_BTN_Y = MARGIN - 2
MODE_BTN_W = 90
MODE_BTN_H = 28

_dragging = False
_drag_path: list[Pos] = []
_drag_seen: set[Pos] = set()


def grid_click_from_mouse(mx, my, top_left, tile_size, rows, cols):
    ox, oy = top_left
    if mx < ox or my < oy: return None
    c = (mx - ox) // tile_size
    r = (my - oy) // tile_size
    if 0 <= r < rows and 0 <= c < cols:
        return (int(r), int(c))
    return None


def _batch_intent_for_mode(state: GameState, path: list[Pos]) -> dict | None:
    if not path:
        return None
    if state.player_action_mode == "PICKUP":
        return {"type": "PICKUP_MINE_BATCH", "positions": path}
    if state.player_action_mode == "COVER":
        return {"type": "COVER_TILE_BATCH", "positions": path}
    return {"type": "PLACE_MINE_BATCH", "positions": path}


def get_intent(events, state: GameState, log_hitboxes=None, log_panel_rect=None):
    global _dragging, _drag_path, _drag_seen
    for e in events:
        if e.type == pygame.QUIT:
            return {"type":"QUIT"}
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            return {"type":"QUIT"}
        if e.type == pygame.MOUSEWHEEL and log_panel_rect is not None:
            mx, my = pygame.mouse.get_pos()
            if log_panel_rect.collidepoint((mx, my)):
                return {"type": "SCROLL_LOG", "delta": -e.y}
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if log_hitboxes:
                for idx, rect in log_hitboxes:
                    if rect.collidepoint(e.pos):
                        return {"type": "SELECT_LOG", "index": idx}
        if e.type == pygame.MOUSEBUTTONDOWN and e.button in (4, 5) and log_panel_rect is not None:
            mx, my = e.pos
            if log_panel_rect.collidepoint((mx, my)):
                return {"type": "SCROLL_LOG", "delta": 1 if e.button == 5 else -1}

        if state.phase == Phase.PLAYER_INPUT and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            place_rect = pygame.Rect(PLACE_BTN_X, MODE_BTN_Y, MODE_BTN_W, MODE_BTN_H)
            pickup_rect = pygame.Rect(PICKUP_BTN_X, MODE_BTN_Y, MODE_BTN_W, MODE_BTN_H)
            cover_rect = pygame.Rect(COVER_BTN_X, MODE_BTN_Y, MODE_BTN_W, MODE_BTN_H)
            if place_rect.collidepoint(e.pos):
                return {"type":"SET_ACTION_MODE", "mode": "PLACE"}
            if pickup_rect.collidepoint(e.pos):
                return {"type":"SET_ACTION_MODE", "mode": "PICKUP"}
            if cover_rect.collidepoint(e.pos):
                return {"type":"SET_ACTION_MODE", "mode": "COVER"}

            skip_rect = pygame.Rect(SKIP_BTN_X, SKIP_BTN_Y, SKIP_BTN_W, SKIP_BTN_H)
            if skip_rect.collidepoint(e.pos):
                return {"type":"SKIP_TURN"}

            pos = grid_click_from_mouse(e.pos[0], e.pos[1], (MARGIN, 60), TILE_SIZE, state.height, state.width)
            if pos is not None:
                _dragging = True
                _drag_path = [pos]
                _drag_seen = {pos}
                continue

        if state.phase == Phase.PLAYER_INPUT and e.type == pygame.MOUSEMOTION and _dragging:
            pos = grid_click_from_mouse(e.pos[0], e.pos[1], (MARGIN, 60), TILE_SIZE, state.height, state.width)
            if pos is not None and pos not in _drag_seen:
                _drag_seen.add(pos)
                _drag_path.append(pos)

        if state.phase == Phase.PLAYER_INPUT and e.type == pygame.MOUSEBUTTONUP and e.button == 1 and _dragging:
            _dragging = False
            path = _drag_path
            _drag_path = []
            _drag_seen = set()
            intent = _batch_intent_for_mode(state, path)
            if intent is not None:
                return intent
    return None
