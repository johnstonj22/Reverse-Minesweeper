# ui_pygame/input.py
import pygame
from core.types import *

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
            pos = grid_click_from_mouse(e.pos[0], e.pos[1], (8,60), 32, state.height, state.width)
            if pos is not None:
                return {"type":"PLACE_MINE", "pos": pos}
    return None
