"""Tests for the Game class."""
import random

import pytest

from machicoro.game import Game
from machicoro.player import Player
from machicoro.strategies import LandmarkFirstStrategy, RandomStrategy


def _game(n: int = 2, verbose: bool = False) -> Game:
    players = [Player(f"P{i}", LandmarkFirstStrategy()) for i in range(n)]
    return Game(players, verbose=verbose)


# ── Construction ───────────────────────────────────────────────────────────


def test_requires_at_least_2_players():
    with pytest.raises(ValueError):
        Game([Player("solo", RandomStrategy())])


def test_initial_turn_number():
    assert _game().turn_number == 0


# ── Full game runs ─────────────────────────────────────────────────────────


def test_game_runs_2_players():
    random.seed(42)
    result = _game(2).run()
    assert result.turns > 0


def test_winner_has_all_landmarks():
    random.seed(42)
    result = _game(2).run()
    if result.winner is not None:
        assert result.winner.is_winner()


def test_game_4_players():
    random.seed(7)
    result = _game(4).run()
    assert result.turns > 0


def test_turn_logs_recorded():
    random.seed(99)
    result = _game(2).run(max_turns=20)
    assert len(result.turn_logs) > 0


def test_turn_log_player_names():
    random.seed(1)
    game = _game(2)
    result = game.run(max_turns=10)
    player_names = {p.name for p in game.players}
    for log in result.turn_logs:
        assert log.player_name in player_names


def test_final_coins_present():
    random.seed(5)
    game = _game(2)
    result = game.run(max_turns=30)
    for player in game.players:
        assert player.name in result.final_coins


def test_player_coins_never_negative():
    random.seed(3)
    game = _game(2)
    game.run(max_turns=100)
    for player in game.players:
        assert player.coins >= 0


# ── Effect resolution ──────────────────────────────────────────────────────


def test_red_card_takes_coins_from_active_player():
    """Café (activation 3) takes 1 coin from the active player."""
    p1 = Player("Roller", RandomStrategy())
    p2 = Player("CafeOwner", RandomStrategy())
    p1.coins = 10
    p2.coins = 0
    # Clear default starting cards so only the café fires on roll 3
    p1.establishments.clear()
    p2.establishments.clear()
    p2.establishments["cafe"] = 1

    game = Game([p1, p2])
    game.current_player_idx = 0  # p1 is active
    game._resolve_effects(p1, 3)

    assert p1.coins == 9
    assert p2.coins == 1


def test_red_card_capped_at_active_players_coins():
    """Player cannot pay more than they have."""
    p1 = Player("Roller", RandomStrategy())
    p2 = Player("RestOwner", RandomStrategy())
    p1.coins = 1
    p2.coins = 0
    p2.add_establishment("family_restaurant")  # activation 9, takes 2

    game = Game([p1, p2])
    game.current_player_idx = 0
    game._resolve_effects(p1, 9)

    assert p1.coins == 0
    assert p2.coins == 1  # capped at what p1 had


def test_blue_card_activates_for_all_players():
    """Wheat Field (activation 1) pays every player."""
    p1 = Player("P1", RandomStrategy())
    p2 = Player("P2", RandomStrategy())
    p1.coins = 0
    p2.coins = 0

    game = Game([p1, p2])
    game._resolve_effects(p1, 1)  # both start with 1 wheat field

    assert p1.coins == 1
    assert p2.coins == 1


def test_green_card_only_active_player():
    """Bakery (activation 2-3) only pays the active player."""
    p1 = Player("Active", RandomStrategy())
    p2 = Player("Inactive", RandomStrategy())
    p1.coins = 0
    p2.coins = 0

    game = Game([p1, p2])
    game._resolve_effects(p1, 2)  # both start with 1 bakery

    assert p1.coins == 1   # active player collects
    assert p2.coins == 0   # inactive does NOT collect green card income


def test_shopping_mall_bonus_on_green_card():
    """Shopping Mall adds +1 to Bakery income for the active player."""
    p1 = Player("Mall", RandomStrategy())
    p2 = Player("Other", RandomStrategy())
    p1.coins = 0
    p2.coins = 0
    p1.landmarks["shopping_mall"] = True

    game = Game([p1, p2])
    game._resolve_effects(p1, 2)  # trigger bakery (activation 2)

    assert p1.coins == 2  # 1 base + 1 mall bonus
    assert p2.coins == 0


def test_shopping_mall_bonus_on_red_card():
    """Shopping Mall adds +1 to Café income for the card *owner*."""
    p1 = Player("Roller", RandomStrategy())
    p2 = Player("CafeOwnerWithMall", RandomStrategy())
    p1.coins = 5
    p2.coins = 0
    # Clear default starting cards so only the café fires on roll 3
    p1.establishments.clear()
    p2.establishments.clear()
    p2.establishments["cafe"] = 1
    p2.landmarks["shopping_mall"] = True

    game = Game([p1, p2])
    game.current_player_idx = 0
    game._resolve_effects(p1, 3)

    # café base 1 + mall bonus 1 = 2 coins taken from p1
    assert p2.coins == 2
    assert p1.coins == 3


def test_stadium_takes_from_all():
    """Stadium (activation 6) takes 2 coins from each other player."""
    p1 = Player("StadiumOwner", RandomStrategy())
    p2 = Player("P2", RandomStrategy())
    p3 = Player("P3", RandomStrategy())
    p1.coins = 0
    p2.coins = 5
    p3.coins = 5
    p1.add_establishment("stadium")

    game = Game([p1, p2, p3])
    game.current_player_idx = 0
    game._resolve_effects(p1, 6)

    assert p1.coins == 4  # 2 from each of 2 players
    assert p2.coins == 3
    assert p3.coins == 3


def test_cheese_factory_uses_ranch_count():
    """Cheese Factory (activation 7) gives 3 coins per Ranch owned."""
    p1 = Player("Farmer", RandomStrategy())
    p2 = Player("Other", RandomStrategy())
    p1.coins = 0
    p1.add_establishment("ranch")    # 1 ranch total
    p1.add_establishment("ranch")    # 2 ranches total
    p1.add_establishment("cheese_factory")

    game = Game([p1, p2])
    game._resolve_effects(p1, 7)

    assert p1.coins == 6  # 3 × 2 ranches


def test_amusement_park_extra_turn_on_doubles():
    """Player with Amusement Park stays active after rolling doubles."""
    random.seed(0)
    p1 = Player("P1", LandmarkFirstStrategy())
    p2 = Player("P2", LandmarkFirstStrategy())
    p1.landmarks["train_station"] = True
    p1.landmarks["amusement_park"] = True
    p1.coins = 100  # ensure can always build

    game = Game([p1, p2])
    game.current_player_idx = 0

    # Force doubles by patching random
    original_randint = random.randint
    call_count = [0]

    def fake_randint(a, b):
        call_count[0] += 1
        # First two calls (2-dice roll): return 3, 3 → doubles
        # Subsequent calls: use real random so game eventually ends
        if call_count[0] <= 2:
            return 3
        return original_randint(a, b)

    random.randint = fake_randint
    try:
        game._take_turn()
    finally:
        random.randint = original_randint

    # Active player index should still be 0 after doubles
    assert game.current_player_idx == 0
