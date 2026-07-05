"""Player class for Machi Koro (街コロ)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from machicoro.landmarks import LANDMARK_DEFS_BY_ID

if TYPE_CHECKING:
    from machicoro.strategies import Strategy


class Player:
    """Represents one player in a game of Machi Koro.

    Each player starts with 3 coins, 1 Wheat Field, and 1 Bakery.
    All four landmarks begin unbuilt.
    """

    def __init__(self, name: str, strategy: "Strategy") -> None:
        self.name = name
        self.strategy = strategy
        self.coins: int = 3
        # card_id → number of copies owned
        self.establishments: Dict[str, int] = {
            "wheat_field": 1,
            "bakery": 1,
        }
        # landmark_id → True if built
        self.landmarks: Dict[str, bool] = {
            lid: False for lid in LANDMARK_DEFS_BY_ID
        }

    # ── Landmark helpers ───────────────────────────────────────────────────

    def has_landmark(self, landmark_id: str) -> bool:
        return self.landmarks.get(landmark_id, False)

    def can_roll_two_dice(self) -> bool:
        return self.has_landmark("train_station")

    def built_landmark_count(self) -> int:
        return sum(1 for built in self.landmarks.values() if built)

    def is_winner(self) -> bool:
        """Return True when all landmarks have been built."""
        return all(self.landmarks.values())

    # ── Establishment helpers ──────────────────────────────────────────────

    def count_establishments(self, card_id: str) -> int:
        return self.establishments.get(card_id, 0)

    def add_establishment(self, card_id: str) -> None:
        self.establishments[card_id] = self.establishments.get(card_id, 0) + 1

    def remove_establishment(self, card_id: str) -> bool:
        """Remove one copy of *card_id*. Returns True on success."""
        if self.establishments.get(card_id, 0) > 0:
            self.establishments[card_id] -= 1
            if self.establishments[card_id] == 0:
                del self.establishments[card_id]
            return True
        return False

    # ── Coin helpers ───────────────────────────────────────────────────────

    def receive_coins(self, amount: int) -> None:
        self.coins += amount

    def pay_coins(self, amount: int) -> int:
        """Pay up to *amount* coins. Returns the actual amount paid."""
        actual = min(self.coins, amount)
        self.coins -= actual
        return actual

    # ── Dunder ────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"Player({self.name!r}, coins={self.coins}, "
            f"landmarks={self.built_landmark_count()}/4)"
        )
