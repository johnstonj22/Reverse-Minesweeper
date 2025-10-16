# ui_pygame/app.py
import pygame
from core.generator import new_game
from core.turn_manager import step
from core.types import Phase, Outcome

def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("Reverse Minesweeper (Prototype)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    from ui_pygame.input import get_intent
    from ui_pygame.view import draw

    state = new_game()
    running = True
    while running:
        events = pygame.event.get()
        intent = get_intent(events, state)
        if intent and intent.get("type") == "QUIT":
            running = False
        else:
            state = step(state, intent)

        draw(screen, state, font)
        pygame.display.flip()
        clock.tick(60)

        if state.phase == Phase.GAME_OVER:
            # simple pause to show result
            pygame.time.wait(1200)
            running = False

    pygame.quit()

if __name__ == "__main__":
    main()
