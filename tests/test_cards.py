"""Tests for card definitions."""
import pytest

from machicoro.cards import (
    CARD_DEFINITIONS,
    CARD_DEFS_BY_ID,
    CardColor,
    EffectType,
)


def test_all_card_ids_unique():
    ids = [c.card_id for c in CARD_DEFINITIONS]
    assert len(ids) == len(set(ids))


def test_card_defs_by_id_contains_all():
    for card in CARD_DEFINITIONS:
        assert card.card_id in CARD_DEFS_BY_ID


def test_wheat_field():
    wf = CARD_DEFS_BY_ID["wheat_field"]
    assert wf.cost == 1
    assert wf.activations == [1]
    assert wf.color == CardColor.BLUE
    assert wf.effect_type == EffectType.BANK_INCOME
    assert wf.base_coins == 1
    assert wf.shopping_mall_bonus is False


def test_bakery():
    b = CARD_DEFS_BY_ID["bakery"]
    assert 2 in b.activations
    assert 3 in b.activations
    assert b.color == CardColor.GREEN
    assert b.shopping_mall_bonus is True


def test_cafe():
    c = CARD_DEFS_BY_ID["cafe"]
    assert c.color == CardColor.RED
    assert c.effect_type == EffectType.PLAYER_INCOME
    assert c.activations == [3]
    assert c.shopping_mall_bonus is True


def test_family_restaurant():
    fr = CARD_DEFS_BY_ID["family_restaurant"]
    assert fr.color == CardColor.RED
    assert 9 in fr.activations
    assert 10 in fr.activations
    assert fr.base_coins == 2


def test_purple_cards_exist():
    for cid in ("stadium", "tv_station", "business_center"):
        assert CARD_DEFS_BY_ID[cid].color == CardColor.PURPLE


def test_stadium():
    s = CARD_DEFS_BY_ID["stadium"]
    assert s.effect_type == EffectType.ALL_PLAYERS_INCOME
    assert s.base_coins == 2
    assert 6 in s.activations


def test_cheese_factory_tags():
    cf = CARD_DEFS_BY_ID["cheese_factory"]
    assert cf.effect_type == EffectType.FACTORY
    assert "ranch" in cf.factory_tags


def test_furniture_factory_tags():
    ff = CARD_DEFS_BY_ID["furniture_factory"]
    assert "forest" in ff.factory_tags
    assert "mine" in ff.factory_tags


def test_fruit_veg_market_tags():
    fv = CARD_DEFS_BY_ID["fruit_veg_market"]
    assert "wheat_field" in fv.factory_tags
    assert "apple_orchard" in fv.factory_tags


def test_mine():
    m = CARD_DEFS_BY_ID["mine"]
    assert m.color == CardColor.BLUE
    assert m.base_coins == 5
    assert m.activations == [9]


def test_activations_are_valid_dice_totals():
    """All activation values must be in the range [1, 12]."""
    for card in CARD_DEFINITIONS:
        for a in card.activations:
            assert 1 <= a <= 12, f"{card.card_id} has invalid activation {a}"
