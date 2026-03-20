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
    enemy_move_delay_ms = 1000
    enemy_think_ready_at = None
    running = True
    while running:
        events = pygame.event.get()
        intent = get_intent(events, state)
        if intent and intent.get("type") == "QUIT":
            running = False
        else:
            now = pygame.time.get_ticks()
            prev_phase = state.phase
            should_advance = True

            # Pause briefly so AI does not reveal instantly after player input.
            if state.phase == Phase.ENEMY_THINK:
                if enemy_think_ready_at is None:
                    enemy_think_ready_at = now + enemy_move_delay_ms
                if now < enemy_think_ready_at:
                    should_advance = False

            if should_advance:
                state = step(state, intent)

                # Start delay when entering enemy think; clear once it moves on.
                if prev_phase != Phase.ENEMY_THINK and state.phase == Phase.ENEMY_THINK:
                    enemy_think_ready_at = pygame.time.get_ticks() + enemy_move_delay_ms
                elif prev_phase == Phase.ENEMY_THINK and state.phase != Phase.ENEMY_THINK:
                    enemy_think_ready_at = None

        draw(screen, state, font)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
