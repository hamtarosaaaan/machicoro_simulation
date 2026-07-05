"""Landmark definitions for Machi Koro (街コロ)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LandmarkDef:
    """Immutable definition of a landmark."""

    landmark_id: str
    name_jp: str
    cost: int
    description: str


LANDMARK_DEFINITIONS: List[LandmarkDef] = [
    LandmarkDef("train_station",  "駅",               4,  "2つのサイコロを振ることができる"),
    LandmarkDef("shopping_mall",  "ショッピングモール", 10, "カフェとパン屋の収入に+1コイン"),
    LandmarkDef("amusement_park", "遊園地",            16, "ゾロ目を出したらもう一度振れる"),
    LandmarkDef("radio_tower",    "ラジオ塔",          22, "1ターンに1回サイコロを振り直せる"),
]

LANDMARK_DEFS_BY_ID: Dict[str, LandmarkDef] = {
    lm.landmark_id: lm for lm in LANDMARK_DEFINITIONS
}
