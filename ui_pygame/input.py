# ui_pygame/input.py
import pygame
from core.types import *
from core.config import MARGIN

SKIP_BTN_X = MARGIN + 700
SKIP_BTN_Y = MARGIN - 2
SKIP_BTN_W = 120
SKIP_BTN_H = 28
PLACE_BTN_X = MARGIN + 500
PICKUP_BTN_X = MARGIN + 600
MODE_BTN_Y = MARGIN - 2
MODE_BTN_W = 90
MODE_BTN_H = 28

def grid_click_from_mouse(mx, my, top_left, tile_size, rows, cols):
    ox, oy = top_left
    if mx < ox or my < oy: return None
    c = (mx - ox) // tile_size
    r = (my - oy) // tile_size
    if 0 <= r < rows and 0 <= c < cols:
        return (int(r), int(c))
    return None

def get_intent(events, state: GameState):
    for e in events:
        if e.type == pygame.QUIT:
            return {"type":"QUIT"}
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            return {"type":"QUIT"}
        if state.phase == Phase.PLAYER_INPUT and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            place_rect = pygame.Rect(PLACE_BTN_X, MODE_BTN_Y, MODE_BTN_W, MODE_BTN_H)
            pickup_rect = pygame.Rect(PICKUP_BTN_X, MODE_BTN_Y, MODE_BTN_W, MODE_BTN_H)
            if place_rect.collidepoint(e.pos):
                return {"type":"SET_ACTION_MODE", "mode": "PLACE"}
            if pickup_rect.collidepoint(e.pos):
                return {"type":"SET_ACTION_MODE", "mode": "PICKUP"}

            if state.mine_stock > 0:
                skip_rect = pygame.Rect(SKIP_BTN_X, SKIP_BTN_Y, SKIP_BTN_W, SKIP_BTN_H)
                if skip_rect.collidepoint(e.pos):
                    return {"type":"SKIP_TURN"}
            pos = grid_click_from_mouse(e.pos[0], e.pos[1], (8,60), 32, state.height, state.width)
            if pos is not None:
                if state.player_action_mode == "PICKUP":
                    return {"type":"PICKUP_MINE", "pos": pos}
                return {"type":"PLACE_MINE", "pos": pos}
    return None
