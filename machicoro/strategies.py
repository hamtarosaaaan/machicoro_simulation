"""AI strategy classes for Machi Koro (街コロ)."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from machicoro.game import GameState
    from machicoro.player import Player


class Strategy(ABC):
    """Abstract base class for player strategies."""

    @abstractmethod
    def choose_dice_count(self, player: "Player", game_state: "GameState") -> int:
        """Return 1 or 2. The Game class enforces that 2 requires train_station."""

    @abstractmethod
    def choose_reroll(
        self,
        player: "Player",
        dice: List[int],
        total: int,
        game_state: "GameState",
    ) -> bool:
        """Return True to use the Radio Tower reroll once per turn."""

    @abstractmethod
    def choose_build(
        self,
        player: "Player",
        affordable_options: List[str],
        game_state: "GameState",
    ) -> Optional[str]:
        """
        Choose what to build/buy this turn, or None to skip.

        *affordable_options* contains card_ids (establishments) and strings of
        the form ``"landmark:<landmark_id>"`` for unbuilt landmarks the player
        can currently afford.
        """

    # ── Default implementations for complex purple-card effects ───────────

    def choose_tv_station_target(
        self,
        player: "Player",
        other_players: List["Player"],
        game_state: "GameState",
    ) -> "Player":
        """Choose which player to take 5 coins from (TV Station)."""
        return max(other_players, key=lambda p: p.coins)

    def choose_business_center_exchange(
        self,
        player: "Player",
        other_players: List["Player"],
        game_state: "GameState",
    ) -> Optional[Tuple[str, str, "Player"]]:
        """
        Choose cards to swap with the Business Center.

        Returns ``(my_card_id, their_card_id, target_player)`` or ``None`` to
        skip the effect entirely.
        """
        from machicoro.cards import CARD_DEFS_BY_ID, CardColor

        for target in sorted(other_players, key=lambda p: p.coins, reverse=True):
            their_cards = [
                cid
                for cid, cnt in target.establishments.items()
                if cnt > 0 and CARD_DEFS_BY_ID[cid].color != CardColor.PURPLE
            ]
            my_cards = [
                cid
                for cid, cnt in player.establishments.items()
                if cnt > 0 and CARD_DEFS_BY_ID[cid].color != CardColor.PURPLE
            ]
            if their_cards and my_cards:
                # Give cheapest card; receive most expensive
                my_card = min(my_cards, key=lambda c: CARD_DEFS_BY_ID[c].cost)
                their_card = max(their_cards, key=lambda c: CARD_DEFS_BY_ID[c].cost)
                return (my_card, their_card, target)
        return None


# ── Concrete strategies ────────────────────────────────────────────────────


class RandomStrategy(Strategy):
    """Makes all decisions at random."""

    def choose_dice_count(self, player: "Player", game_state: "GameState") -> int:
        if player.can_roll_two_dice():
            return random.choice([1, 2])
        return 1

    def choose_reroll(
        self,
        player: "Player",
        dice: List[int],
        total: int,
        game_state: "GameState",
    ) -> bool:
        if not player.has_landmark("radio_tower"):
            return False
        return random.choice([True, False])

    def choose_build(
        self,
        player: "Player",
        affordable_options: List[str],
        game_state: "GameState",
    ) -> Optional[str]:
        if not affordable_options:
            return None
        return random.choice(affordable_options + [None])


class LandmarkFirstStrategy(Strategy):
    """
    Builds landmarks in ascending cost order as soon as they are affordable,
    then buys the most expensive available card.
    """

    _LANDMARK_ORDER = [
        "train_station",
        "shopping_mall",
        "amusement_park",
        "radio_tower",
    ]

    def choose_dice_count(self, player: "Player", game_state: "GameState") -> int:
        return 2 if player.can_roll_two_dice() else 1

    def choose_reroll(
        self,
        player: "Player",
        dice: List[int],
        total: int,
        game_state: "GameState",
    ) -> bool:
        if not player.has_landmark("radio_tower"):
            return False
        return total <= 3

    def choose_build(
        self,
        player: "Player",
        affordable_options: List[str],
        game_state: "GameState",
    ) -> Optional[str]:
        if not affordable_options:
            return None
        from machicoro.cards import CARD_DEFS_BY_ID

        for lid in self._LANDMARK_ORDER:
            option = f"landmark:{lid}"
            if option in affordable_options:
                return option

        card_options = [o for o in affordable_options if not o.startswith("landmark:")]
        if card_options:
            return max(card_options, key=lambda c: CARD_DEFS_BY_ID[c].cost)
        return None


class IncomeMaxStrategy(Strategy):
    """
    Maximises expected coin income by prioritising high-yield cards.
    Buys the Train Station first once affordable to unlock two-dice rolls,
    then builds remaining landmarks once a buffer of coins is available.
    """

    _CARD_PRIORITY = [
        "mine",
        "cheese_factory",
        "furniture_factory",
        "apple_orchard",
        "forest",
        "convenience_store",
        "ranch",
        "fruit_veg_market",
        "family_restaurant",
        "cafe",
        "wheat_field",
        "bakery",
        # Purple establishments
        "stadium",
        "tv_station",
        "business_center",
    ]

    # Buffer to keep after buying a landmark (to continue buying income cards)
    _LANDMARK_BUFFER = 4

    def choose_dice_count(self, player: "Player", game_state: "GameState") -> int:
        return 2 if player.can_roll_two_dice() else 1

    def choose_reroll(
        self,
        player: "Player",
        dice: List[int],
        total: int,
        game_state: "GameState",
    ) -> bool:
        if not player.has_landmark("radio_tower"):
            return False
        return total <= 4

    def choose_build(
        self,
        player: "Player",
        affordable_options: List[str],
        game_state: "GameState",
    ) -> Optional[str]:
        if not affordable_options:
            return None
        from machicoro.cards import CARD_DEFS_BY_ID
        from machicoro.landmarks import LANDMARK_DEFS_BY_ID

        card_options = [o for o in affordable_options if not o.startswith("landmark:")]
        landmark_options = [o for o in affordable_options if o.startswith("landmark:")]

        # 1. Always grab the Train Station first (enables 2-dice rolls)
        if "landmark:train_station" in landmark_options:
            return "landmark:train_station"

        # 2. Build the next landmark when we have the cost + a buffer
        landmark_order = ["shopping_mall", "amusement_park", "radio_tower"]
        for lid in landmark_order:
            opt = f"landmark:{lid}"
            if opt in landmark_options:
                lm_cost = LANDMARK_DEFS_BY_ID[lid].cost
                if player.coins >= lm_cost + self._LANDMARK_BUFFER:
                    return opt

        # 3. Buy income cards in priority order (limit 2 copies each)
        for cid in self._CARD_PRIORITY:
            if cid in card_options and player.count_establishments(cid) < 2:
                return cid

        # 4. Fall back to any landmark we can afford
        if landmark_options:
            sorted_landmarks = sorted(
                landmark_options,
                key=lambda o: LANDMARK_DEFS_BY_ID[o[9:]].cost,
            )
            return sorted_landmarks[0]

        return None
