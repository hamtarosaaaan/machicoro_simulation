"""Card (establishment) definitions for Machi Koro (街コロ)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class CardColor(Enum):
    """Card colour determines when the effect activates."""

    BLUE = "blue"      # Primary Industry  — activates on *any* player's turn
    GREEN = "green"    # Secondary Industry — activates only on the *owner's* turn
    RED = "red"        # Restaurant         — activates on *other* players' turns
    PURPLE = "purple"  # Major Establishment — owner's turn; limit 1 per player


class EffectType(Enum):
    """How a card's effect is resolved."""

    BANK_INCOME = "bank_income"                    # Owner receives coins from bank
    FACTORY = "factory"                            # Owner receives coins × matching cards owned
    PLAYER_INCOME = "player_income"                # Owner takes coins from active player (Red)
    ALL_PLAYERS_INCOME = "all_players_income"      # Owner takes coins from *every* other player
    CHOOSE_PLAYER_TAKE = "choose_player_take"      # Owner takes coins from one chosen player
    EXCHANGE_CARD = "exchange_card"                # Owner swaps a card with another player


@dataclass
class CardDef:
    """Immutable definition of one type of establishment."""

    card_id: str
    name_jp: str
    cost: int
    activations: List[int]     # Dice totals that trigger this card
    color: CardColor
    effect_type: EffectType
    base_coins: int            # Coins per card (or multiplier for FACTORY)
    factory_tags: List[str] = field(default_factory=list)
    # Whether Shopping Mall landmark adds +1 coin to this card's activation
    shopping_mall_bonus: bool = False


# ---------------------------------------------------------------------------
# All card definitions for the base game
# ---------------------------------------------------------------------------
CARD_DEFINITIONS: List[CardDef] = [
    # ── Blue cards (Primary Industry) ──────────────────────────────────────
    CardDef("wheat_field",   "麦畑",   1, [1],       CardColor.BLUE,   EffectType.BANK_INCOME,   1),
    CardDef("ranch",         "牧場",   1, [2],       CardColor.BLUE,   EffectType.BANK_INCOME,   1),
    CardDef("forest",        "森林",   3, [5],       CardColor.BLUE,   EffectType.BANK_INCOME,   1),
    CardDef("mine",          "鉱山",   6, [9],       CardColor.BLUE,   EffectType.BANK_INCOME,   5),
    CardDef("apple_orchard", "りんご園", 3, [10],    CardColor.BLUE,   EffectType.BANK_INCOME,   3),

    # ── Green cards (Secondary Industry) ───────────────────────────────────
    CardDef(
        "bakery", "パン屋", 1, [2, 3],
        CardColor.GREEN, EffectType.BANK_INCOME, 1,
        shopping_mall_bonus=True,
    ),
    CardDef(
        "convenience_store", "コンビニ", 2, [4],
        CardColor.GREEN, EffectType.BANK_INCOME, 3,
        shopping_mall_bonus=True,
    ),
    CardDef(
        "cheese_factory", "チーズ工場", 5, [7],
        CardColor.GREEN, EffectType.FACTORY, 3,
        factory_tags=["ranch"],
    ),
    CardDef(
        "furniture_factory", "家具工場", 3, [8],
        CardColor.GREEN, EffectType.FACTORY, 3,
        factory_tags=["forest", "mine"],
    ),
    CardDef(
        "fruit_veg_market", "青果市場", 2, [11, 12],
        CardColor.GREEN, EffectType.FACTORY, 2,
        factory_tags=["wheat_field", "apple_orchard"],
    ),

    # ── Red cards (Restaurant) ──────────────────────────────────────────────
    CardDef(
        "cafe", "カフェ", 2, [3],
        CardColor.RED, EffectType.PLAYER_INCOME, 1,
        shopping_mall_bonus=True,
    ),
    CardDef(
        "family_restaurant", "ファミリーレストラン", 3, [9, 10],
        CardColor.RED, EffectType.PLAYER_INCOME, 2,
        shopping_mall_bonus=True,
    ),

    # ── Purple cards (Major Establishment) ─────────────────────────────────
    CardDef("stadium",         "スタジアム",       6, [6], CardColor.PURPLE, EffectType.ALL_PLAYERS_INCOME, 2),
    CardDef("tv_station",      "テレビ局",         7, [6], CardColor.PURPLE, EffectType.CHOOSE_PLAYER_TAKE, 5),
    CardDef("business_center", "ビジネスセンター", 8, [6], CardColor.PURPLE, EffectType.EXCHANGE_CARD,      0),
]

CARD_DEFS_BY_ID: Dict[str, CardDef] = {c.card_id: c for c in CARD_DEFINITIONS}
