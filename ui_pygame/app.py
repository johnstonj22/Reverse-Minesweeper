# ui_pygame/app.py
import pygame
from copy import deepcopy
from core.generator import new_game
from core.turn_manager import step
from core.types import Phase

def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("Reverse Minesweeper (Prototype)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    from ui_pygame.input import get_intent
    from ui_pygame.view import draw

    state = new_game()
    timeline = [{"label": "Start", "detail": "Initial board state.", "state": deepcopy(state)}]
    active_log_index = 0
    log_hitboxes = []
    log_panel_rect = None
    log_scroll_start = 0

    def push_timeline(label: str, detail: str = ""):
        nonlocal active_log_index, log_scroll_start
        timeline.append({"label": label, "detail": detail, "state": deepcopy(state)})
        active_log_index = len(timeline) - 1
        log_scroll_start = max(0, len(timeline) - 1)

    enemy_move_delay_ms = 1000
    enemy_think_ready_at = None
    running = True
    while running:
        events = pygame.event.get()
        intent = get_intent(events, state, log_hitboxes, log_panel_rect)
        if intent and intent.get("type") == "QUIT":
            running = False
        elif intent and intent.get("type") == "SCROLL_LOG":
            log_scroll_start += int(intent.get("delta", 0))
        elif intent and intent.get("type") == "SELECT_LOG":
            idx = max(0, min(intent["index"], len(timeline) - 1))
            active_log_index = idx
            log_scroll_start = idx
            state = deepcopy(timeline[idx]["state"])
            enemy_think_ready_at = None
        else:
            # When viewing historical snapshots, ignore gameplay intents.
            if active_log_index == len(timeline) - 1:
                now = pygame.time.get_ticks()
                prev_phase = state.phase
                pre_revealed = set(state.revealed)
                pre_enemy_hp = state.enemy_hp
                pre_mines = set(state.mines)
                should_advance = True

                # Pause briefly so AI does not reveal instantly after player input.
                if state.phase == Phase.ENEMY_THINK:
                    if enemy_think_ready_at is None:
                        enemy_think_ready_at = now + enemy_move_delay_ms
                    if now < enemy_think_ready_at:
                        should_advance = False

                if should_advance:
                    state = step(state, intent)

                    # Keep a delay before every AI action while ENEMY_THINK is active.
                    if state.phase == Phase.ENEMY_THINK:
                        enemy_think_ready_at = pygame.time.get_ticks() + enemy_move_delay_ms
                    else:
                        enemy_think_ready_at = None

                    # Log notable actions as timeline snapshots.
                    if intent and intent.get("type") == "PLACE_MINE":
                        pos = intent.get("pos")
                        if pos in state.mines and pos not in pre_mines:
                            push_timeline(
                                f"Player placed mine at {pos}",
                                f"Mode=PLACE. Mine stock now {state.mine_stock}.",
                            )
                    elif intent and intent.get("type") == "PLACE_MINE_BATCH":
                        added = list(state.mines - pre_mines)
                        if added:
                            push_timeline(
                                f"Player placed {len(added)} mine(s) via drag",
                                f"Batch PLACE. Mine stock now {state.mine_stock}.",
                            )
                    elif intent and intent.get("type") == "PICKUP_MINE":
                        pos = intent.get("pos")
                        if pos in pre_mines and pos not in state.mines:
                            push_timeline(
                                f"Player picked up mine at {pos}",
                                f"Mode=PICKUP. Mine stock unchanged at {state.mine_stock}.",
                            )
                    elif intent and intent.get("type") == "PICKUP_MINE_BATCH":
                        removed = list(pre_mines - state.mines)
                        if removed:
                            push_timeline(
                                f"Player picked up {len(removed)} mine(s) via drag",
                                f"Batch PICKUP. Mine stock unchanged at {state.mine_stock}.",
                            )
                    elif intent and intent.get("type") == "COVER_TILE":
                        pos = intent.get("pos")
                        if pos not in state.revealed and pos in pre_revealed:
                            push_timeline(
                                f"Player covered tile at {pos}",
                                f"Recover stock now {state.recover_stock}.",
                            )
                    elif intent and intent.get("type") == "COVER_TILE_BATCH":
                        covered = list(pre_revealed - state.revealed)
                        if covered:
                            push_timeline(
                                f"Player covered {len(covered)} tile(s) via drag",
                                f"Batch COVER. Recover stock now {state.recover_stock}.",
                            )
                    elif intent and intent.get("type") == "SKIP_TURN":
                        push_timeline(
                            "Player skipped turn",
                            f"Skipped with mine stock {state.mine_stock} and recover stock {state.recover_stock}.",
                        )

                    if prev_phase == Phase.ENEMY_THINK and state.phase in (Phase.ENEMY_THINK, Phase.CHECK_WINLOSE):
                        newly = list(state.revealed - pre_revealed)
                        move = state.last_enemy_move
                        rationale = ""
                        if move is not None:
                            rationale = f"AI rationale: {move.rationale}; p={move.chosen_p:.3f}."
                        if state.enemy_hp < pre_enemy_hp:
                            if newly:
                                push_timeline(
                                    f"AI hit mine at {newly[0]} ({len(newly)} revealed)",
                                    rationale or "AI revealed a mined tile.",
                                )
                            else:
                                push_timeline("AI hit a mine", rationale or "AI triggered mine damage.")
                        elif newly:
                            push_timeline(
                                f"AI revealed {len(newly)} tile(s), first {newly[0]}",
                                rationale or "AI completed a reveal move.",
                            )
                        else:
                            push_timeline("AI had no reveal move", rationale or "No hidden tile selected.")

        if active_log_index == len(timeline) - 1:
            timeline[-1]["state"] = deepcopy(state)

        log_hitboxes, log_panel_rect, log_scroll_start, max_start = draw(
            screen, state, font, timeline, active_log_index, log_scroll_start
        )
        log_scroll_start = max(0, min(log_scroll_start, max_start))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
