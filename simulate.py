#!/usr/bin/env python3
"""
街コロ (Machi Koro) シミュレーター
====================================
Run multiple games between AI players with different strategies and report
win rates plus average game length.

Usage examples
--------------
# 1 000 games, 2 players using the default strategies
python simulate.py

# 500 games, 3 players mixing all three strategies, fixed seed, verbose first game
python simulate.py -n 500 -p 3 -s random landmark income --seed 42 -v
"""
from __future__ import annotations

import argparse
import random
from collections import defaultdict
from typing import Dict, List, Optional

from machicoro.game import Game
from machicoro.player import Player
from machicoro.strategies import IncomeMaxStrategy, LandmarkFirstStrategy, RandomStrategy

STRATEGY_MAP = {
    "random":   RandomStrategy,
    "landmark": LandmarkFirstStrategy,
    "income":   IncomeMaxStrategy,
}


def run_simulation(
    num_games: int,
    num_players: int,
    strategy_names: List[str],
    seed: Optional[int] = None,
    verbose: bool = False,
) -> None:
    if seed is not None:
        random.seed(seed)

    wins: Dict[str, int] = defaultdict(int)
    total_turns: List[int] = []
    timeouts = 0

    for game_idx in range(num_games):
        players = []
        for i in range(num_players):
            sname = strategy_names[i % len(strategy_names)]
            players.append(Player(f"{sname}_{i}", STRATEGY_MAP[sname]()))

        show_verbose = verbose and game_idx == 0
        game = Game(players, verbose=show_verbose)
        result = game.run()

        total_turns.append(result.turns)
        if result.winner is not None:
            wins[result.winner.strategy.__class__.__name__] += 1
        else:
            timeouts += 1

    avg = sum(total_turns) / len(total_turns)

    print(f"\n{'='*60}")
    print(f"  街コロ シミュレーション結果")
    print(f"  ゲーム数: {num_games}  プレイヤー数: {num_players}")
    print(f"{'='*60}")
    print(f"  平均ターン数: {avg:.1f}")
    print(f"  タイムアウト (勝者なし): {timeouts}")
    print()
    print("  勝率:")
    total_wins = sum(wins.values())
    for strat_name, count in sorted(wins.items(), key=lambda x: -x[1]):
        rate = count / num_games * 100
        print(f"    {strat_name:<30} {count:>5} 勝  ({rate:5.1f}%)")
    if total_wins < num_games:
        undecided = num_games - total_wins
        print(f"    {'(引き分け/タイムアウト)':<30} {undecided:>5} 回  ({undecided/num_games*100:5.1f}%)")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="街コロ (Machi Koro) ボードゲーム シミュレーター",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-n", "--num-games",
        type=int, default=1000,
        help="シミュレーションするゲーム数 (デフォルト: 1000)",
    )
    parser.add_argument(
        "-p", "--players",
        type=int, default=2,
        help="プレイヤー数 (デフォルト: 2)",
    )
    parser.add_argument(
        "-s", "--strategies",
        nargs="+",
        choices=list(STRATEGY_MAP.keys()),
        default=["landmark", "income"],
        help="使用する戦略 (プレイヤーに順番に割り当てられる)",
    )
    parser.add_argument(
        "--seed",
        type=int, default=None,
        help="乱数シード (再現性のため)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="最初のゲームの詳細ログを表示する",
    )
    args = parser.parse_args()

    run_simulation(
        num_games=args.num_games,
        num_players=args.players,
        strategy_names=args.strategies,
        seed=args.seed,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
