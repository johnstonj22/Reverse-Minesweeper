from __future__ import annotations

import json
from datetime import datetime, timezone
from multiprocessing import Pool, cpu_count
from pathlib import Path

from core.generator import new_game
from core.player_ai import choose_player_intent
from core.turn_manager import step
from core.types import GameState, Outcome, Phase


def _play_one_game(seed: int, max_steps: int, fast_policy: bool, counter_probe_budget: int) -> dict:
    state: GameState = new_game(seed)
    steps = 0
    player_actions = 0
    enemy_actions = 0

    while state.phase != Phase.GAME_OVER and steps < max_steps:
        intent = None
        if state.phase == Phase.PLAYER_INPUT:
            intent = choose_player_intent(
                state,
                fast_mode=fast_policy,
                counter_probe_budget=counter_probe_budget,
            )
            player_actions += 1
        elif state.phase == Phase.ENEMY_THINK:
            enemy_actions += 1

        state = step(state, intent)
        steps += 1

    timed_out = state.phase != Phase.GAME_OVER
    final_outcome = Outcome.ENEMY_WIN.name if timed_out else state.outcome.name

    return {
        "seed": seed,
        "timed_out": timed_out,
        "outcome": final_outcome,
        "steps": steps,
        "enemy_hp_end": state.enemy_hp,
        "revealed_tiles_end": len(state.revealed),
        "mine_count_end": len(state.mines),
        "player_actions": player_actions,
        "enemy_actions": enemy_actions,
    }


def _play_one_game_worker(args: tuple[int, int, bool, int]) -> dict:
    seed, max_steps, fast_policy, counter_probe_budget = args
    return _play_one_game(seed, max_steps, fast_policy, counter_probe_budget)


def run_simulation(
    num_games: int,
    seed_start: int = 0,
    output_path: str = "sim_results.json",
    max_steps_per_game: int = 20000,
    workers: int = 1,
    fast_policy: bool = False,
    counter_probe_budget: int = 24,
) -> dict:
    seeds = [seed_start + i for i in range(num_games)]
    tasks = [(seed, max_steps_per_game, fast_policy, counter_probe_budget) for seed in seeds]

    if workers <= 0:
        workers = max(1, cpu_count() - 1)

    if workers == 1:
        games = [_play_one_game_worker(task) for task in tasks]
    else:
        try:
            with Pool(processes=workers) as pool:
                games = list(pool.imap_unordered(_play_one_game_worker, tasks, chunksize=1))
            games.sort(key=lambda g: g["seed"])
        except (PermissionError, OSError):
            # Some constrained environments disallow multiprocessing pipes.
            workers = 1
            games = [_play_one_game_worker(task) for task in tasks]

    player_wins = sum(1 for g in games if g["outcome"] == Outcome.PLAYER_WIN.name)
    enemy_wins = len(games) - player_wins
    timeouts = sum(1 for g in games if g["timed_out"])
    total_steps = sum(g["steps"] for g in games)

    summary = {
        "games": num_games,
        "seed_start": seed_start,
        "player_wins": player_wins,
        "enemy_wins": enemy_wins,
        "timeouts": timeouts,
        "player_win_rate": (player_wins / num_games) if num_games > 0 else 0.0,
        "avg_steps": (total_steps / num_games) if num_games > 0 else 0.0,
        "player_ai_policy": "counter_safe_v1",
        "fast_policy": fast_policy,
        "counter_probe_budget": counter_probe_budget,
        "workers": workers,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    payload = {"summary": summary, "games": games}
    out = Path(output_path)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
