# main.py
from __future__ import annotations

import argparse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reverse Minesweeper")
    parser.add_argument(
        "--simulate",
        type=int,
        default=0,
        help="Run N headless simulation games instead of launching the UI.",
    )
    parser.add_argument(
        "--seed-start",
        type=int,
        default=0,
        help="Starting seed for simulation runs.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="sim_results.json",
        help="Output JSON file path for simulation results.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=20000,
        help="Maximum step count per simulated game.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Simulation worker processes (1 = single-process, 0 = auto).",
    )
    parser.add_argument(
        "--fast-policy",
        action="store_true",
        help="Use faster player-AI policy branch (reduced counter search).",
    )
    parser.add_argument(
        "--counter-probes",
        type=int,
        default=24,
        help="Maximum counter-probe evaluations per player decision.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.simulate and args.simulate > 0:
        from core.sim_runner import run_simulation

        payload = run_simulation(
            num_games=args.simulate,
            seed_start=args.seed_start,
            output_path=args.out,
            max_steps_per_game=args.max_steps,
            workers=args.workers,
            fast_policy=args.fast_policy,
            counter_probe_budget=args.counter_probes,
        )
        s = payload["summary"]
        print(
            f"Sim complete: games={s['games']} "
            f"player_wins={s['player_wins']} enemy_wins={s['enemy_wins']} "
            f"timeouts={s['timeouts']} win_rate={s['player_win_rate']:.3f} "
            f"avg_steps={s['avg_steps']:.1f} workers={s['workers']} "
            f"fast_policy={s['fast_policy']} probes={s['counter_probe_budget']} out={args.out}"
        )
        return

    from ui_pygame.app import main as ui_main

    ui_main()


if __name__ == "__main__":
    main()
