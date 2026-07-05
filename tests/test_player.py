"""Tests for the Player class."""
import pytest

from machicoro.player import Player
from machicoro.strategies import RandomStrategy


def _player(name: str = "Test") -> Player:
    return Player(name, RandomStrategy())


# ── Initial state ──────────────────────────────────────────────────────────


def test_initial_coins():
    assert _player().coins == 3


def test_initial_establishments():
    p = _player()
    assert p.count_establishments("wheat_field") == 1
    assert p.count_establishments("bakery") == 1


def test_initial_landmarks_all_unbuilt():
    p = _player()
    for lid, built in p.landmarks.items():
        assert not built, f"Landmark {lid!r} should start unbuilt"


def test_initial_not_winner():
    assert not _player().is_winner()


# ── Coin operations ────────────────────────────────────────────────────────


def test_receive_coins():
    p = _player()
    p.receive_coins(5)
    assert p.coins == 8


def test_pay_coins_exact():
    p = _player()
    paid = p.pay_coins(3)
    assert paid == 3
    assert p.coins == 0


def test_pay_coins_partial():
    p = _player()
    paid = p.pay_coins(100)
    assert paid == 3
    assert p.coins == 0


def test_pay_coins_zero():
    p = _player()
    paid = p.pay_coins(0)
    assert paid == 0
    assert p.coins == 3


# ── Establishment operations ───────────────────────────────────────────────


def test_add_establishment():
    p = _player()
    p.add_establishment("cafe")
    assert p.count_establishments("cafe") == 1


def test_add_establishment_multiple():
    p = _player()
    p.add_establishment("ranch")
    p.add_establishment("ranch")
    assert p.count_establishments("ranch") == 2


def test_remove_establishment_success():
    p = _player()
    p.add_establishment("cafe")
    assert p.remove_establishment("cafe") is True
    assert p.count_establishments("cafe") == 0


def test_remove_establishment_cleans_dict():
    p = _player()
    p.add_establishment("cafe")
    p.remove_establishment("cafe")
    assert "cafe" not in p.establishments


def test_remove_establishment_nonexistent():
    p = _player()
    assert p.remove_establishment("mine") is False


def test_remove_one_of_many():
    p = _player()
    p.add_establishment("ranch")
    p.add_establishment("ranch")
    p.remove_establishment("ranch")
    assert p.count_establishments("ranch") == 1


# ── Landmark helpers ───────────────────────────────────────────────────────


def test_has_landmark_false():
    p = _player()
    assert not p.has_landmark("train_station")
    assert not p.can_roll_two_dice()


def test_has_landmark_true():
    p = _player()
    p.landmarks["train_station"] = True
    assert p.has_landmark("train_station")
    assert p.can_roll_two_dice()


def test_built_landmark_count():
    p = _player()
    assert p.built_landmark_count() == 0
    p.landmarks["train_station"] = True
    p.landmarks["shopping_mall"] = True
    assert p.built_landmark_count() == 2


def test_is_winner_all_built():
    p = _player()
    for lid in p.landmarks:
        p.landmarks[lid] = True
    assert p.is_winner()


def test_is_winner_partial():
    p = _player()
    p.landmarks["train_station"] = True
    assert not p.is_winner()
