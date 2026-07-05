"""Game engine for Machi Koro (街コロ)."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from machicoro.cards import CARD_DEFS_BY_ID, CardColor, EffectType
from machicoro.landmarks import LANDMARK_DEFS_BY_ID
from machicoro.player import Player


@dataclass
class GameState:
    """Read-only snapshot of the game passed to strategy methods."""

    players: List[Player]
    current_player_idx: int
    turn_number: int


@dataclass
class TurnLog:
    """Record of one player's turn."""

    turn_number: int
    player_name: str
    dice: List[int]
    total: int
    rerolled: bool
    coins_before: int
    coins_after: int
    built: Optional[str]  # card_id / "landmark:..." / None


@dataclass
class GameResult:
    """Outcome of a completed game."""

    winner: Optional[Player]
    turns: int
    turn_logs: List[TurnLog] = field(default_factory=list)
    final_coins: Dict[str, int] = field(default_factory=dict)


class Game:
    """Runs a full game of Machi Koro between two or more players."""

    def __init__(self, players: List[Player], verbose: bool = False) -> None:
        if len(players) < 2:
            raise ValueError("Machi Koro requires at least 2 players.")
        self.players = players
        self.verbose = verbose
        self.current_player_idx: int = 0
        self.turn_number: int = 0
        self._turn_logs: List[TurnLog] = []

    # ── Public API ─────────────────────────────────────────────────────────

    def run(self, max_turns: int = 500) -> GameResult:
        """Play the game to completion (or *max_turns*). Returns a GameResult."""
        winner: Optional[Player] = None
        while self.turn_number < max_turns:
            winner = self._take_turn()
            if winner is not None:
                break

        return GameResult(
            winner=winner,
            turns=self.turn_number,
            turn_logs=list(self._turn_logs),
            final_coins={p.name: p.coins for p in self.players},
        )

    # ── Turn execution ─────────────────────────────────────────────────────

    def _take_turn(self) -> Optional[Player]:
        """Execute the current player's turn. Returns the winner or None."""
        player = self.players[self.current_player_idx]
        self.turn_number += 1
        game_state = self._get_game_state()

        # 1. Dice roll ──────────────────────────────────────────────────────
        dice_count = player.strategy.choose_dice_count(player, game_state)
        if not player.can_roll_two_dice():
            dice_count = 1

        dice = [random.randint(1, 6) for _ in range(dice_count)]
        total = sum(dice)
        rerolled = False

        # Radio Tower: one optional reroll per turn
        if player.has_landmark("radio_tower"):
            if player.strategy.choose_reroll(player, dice, total, game_state):
                dice = [random.randint(1, 6) for _ in range(dice_count)]
                total = sum(dice)
                rerolled = True

        if self.verbose:
            reroll_note = " (振り直し)" if rerolled else ""
            print(
                f"ターン {self.turn_number} [{player.name}]: "
                f"サイコロ {dice} = {total}{reroll_note}"
            )

        coins_before = player.coins

        # 2. Card effects ───────────────────────────────────────────────────
        self._resolve_effects(player, total)

        # 3. Build phase ────────────────────────────────────────────────────
        built = self._build_phase(player)

        self._turn_logs.append(
            TurnLog(
                turn_number=self.turn_number,
                player_name=player.name,
                dice=list(dice),
                total=total,
                rerolled=rerolled,
                coins_before=coins_before,
                coins_after=player.coins,
                built=built,
            )
        )

        # 4. Win check ──────────────────────────────────────────────────────
        if player.is_winner():
            if self.verbose:
                print(f"\n🎉 {player.name} がターン {self.turn_number} で勝利！")
            return player

        # 5. Advance turn (Amusement Park grants an extra turn on doubles) ──
        doubles = len(dice) == 2 and dice[0] == dice[1]
        if not (player.has_landmark("amusement_park") and doubles):
            self.current_player_idx = (
                (self.current_player_idx + 1) % len(self.players)
            )
        elif self.verbose:
            print(f"  {player.name} はゾロ目でもう一度振れる！")

        return None

    # ── Effect resolution ──────────────────────────────────────────────────

    def _resolve_effects(self, active_player: Player, total: int) -> None:
        """
        Resolve all card effects triggered by *total* in the correct order:

        1. Red  — inactive players take from active player (clockwise order)
        2. Blue — all players receive from bank
        3. Green — active player only receives from bank (or factory)
        4. Purple — active player's major establishment effect
        """
        active_idx = self.players.index(active_player)
        # Players in clockwise order starting *after* the active player
        ordered_others: List[Player] = (
            self.players[active_idx + 1:] + self.players[:active_idx]
        )

        # ── Red cards ──────────────────────────────────────────────────────
        for owner in ordered_others:
            for card_id, count in list(owner.establishments.items()):
                card_def = CARD_DEFS_BY_ID[card_id]
                if card_def.color != CardColor.RED or total not in card_def.activations:
                    continue
                coins_per = card_def.base_coins
                if card_def.shopping_mall_bonus and owner.has_landmark("shopping_mall"):
                    coins_per += 1
                amount = coins_per * count
                actual = active_player.pay_coins(amount)
                owner.receive_coins(actual)
                if self.verbose:
                    print(
                        f"  {owner.name}: {card_def.name_jp} ×{count} → "
                        f"{active_player.name} から {actual} コイン取得"
                    )

        # ── Blue cards ─────────────────────────────────────────────────────
        for player in self.players:
            for card_id, count in list(player.establishments.items()):
                card_def = CARD_DEFS_BY_ID[card_id]
                if card_def.color != CardColor.BLUE or total not in card_def.activations:
                    continue
                amount = card_def.base_coins * count
                player.receive_coins(amount)
                if self.verbose:
                    print(
                        f"  {player.name}: {card_def.name_jp} ×{count} → "
                        f"銀行から +{amount} コイン"
                    )

        # ── Green cards ────────────────────────────────────────────────────
        for card_id, count in list(active_player.establishments.items()):
            card_def = CARD_DEFS_BY_ID[card_id]
            if card_def.color != CardColor.GREEN or total not in card_def.activations:
                continue
            if card_def.effect_type == EffectType.BANK_INCOME:
                coins_per = card_def.base_coins
                if (
                    card_def.shopping_mall_bonus
                    and active_player.has_landmark("shopping_mall")
                ):
                    coins_per += 1
                amount = coins_per * count
                active_player.receive_coins(amount)
                if self.verbose:
                    print(
                        f"  {active_player.name}: {card_def.name_jp} ×{count} → "
                        f"銀行から +{amount} コイン"
                    )
            elif card_def.effect_type == EffectType.FACTORY:
                tag_count = sum(
                    active_player.count_establishments(tag)
                    for tag in card_def.factory_tags
                )
                amount = card_def.base_coins * tag_count * count
                active_player.receive_coins(amount)
                if self.verbose:
                    print(
                        f"  {active_player.name}: {card_def.name_jp} ×{count} "
                        f"(対象 {tag_count} 枚) → 銀行から +{amount} コイン"
                    )

        # ── Purple cards ───────────────────────────────────────────────────
        game_state = self._get_game_state()
        for card_id, count in list(active_player.establishments.items()):
            card_def = CARD_DEFS_BY_ID[card_id]
            if card_def.color != CardColor.PURPLE or total not in card_def.activations:
                continue
            if card_def.effect_type == EffectType.ALL_PLAYERS_INCOME:
                for other in ordered_others:
                    actual = other.pay_coins(card_def.base_coins)
                    active_player.receive_coins(actual)
                    if self.verbose:
                        print(
                            f"  {active_player.name}: {card_def.name_jp} → "
                            f"{other.name} から {actual} コイン取得"
                        )
            elif card_def.effect_type == EffectType.CHOOSE_PLAYER_TAKE:
                if ordered_others:
                    target = active_player.strategy.choose_tv_station_target(
                        active_player, ordered_others, game_state
                    )
                    actual = target.pay_coins(card_def.base_coins)
                    active_player.receive_coins(actual)
                    if self.verbose:
                        print(
                            f"  {active_player.name}: {card_def.name_jp} → "
                            f"{target.name} から {actual} コイン取得"
                        )
            elif card_def.effect_type == EffectType.EXCHANGE_CARD:
                result = active_player.strategy.choose_business_center_exchange(
                    active_player, ordered_others, game_state
                )
                if result is not None:
                    my_card, their_card, target = result
                    if active_player.remove_establishment(
                        my_card
                    ) and target.remove_establishment(their_card):
                        active_player.add_establishment(their_card)
                        target.add_establishment(my_card)
                        if self.verbose:
                            print(
                                f"  {active_player.name}: {card_def.name_jp} → "
                                f"{my_card} と {their_card} を交換 ({target.name})"
                            )

    # ── Build phase ────────────────────────────────────────────────────────

    def _build_phase(self, player: Player) -> Optional[str]:
        """Player optionally buys one establishment or landmark."""
        affordable = self._get_affordable_options(player)
        game_state = self._get_game_state()
        choice = player.strategy.choose_build(player, affordable, game_state)

        if choice is None:
            return None

        if choice.startswith("landmark:"):
            landmark_id = choice[len("landmark:"):]
            lm_def = LANDMARK_DEFS_BY_ID[landmark_id]
            player.pay_coins(lm_def.cost)
            player.landmarks[landmark_id] = True
            if self.verbose:
                print(
                    f"  {player.name} がランドマーク建設: "
                    f"{lm_def.name_jp} (コスト {lm_def.cost})"
                )
        else:
            card_def = CARD_DEFS_BY_ID[choice]
            # Purple cards: each player may own at most one copy
            if (
                card_def.color == CardColor.PURPLE
                and player.count_establishments(choice) >= 1
            ):
                return None
            player.pay_coins(card_def.cost)
            player.add_establishment(choice)
            if self.verbose:
                print(
                    f"  {player.name} がカード購入: "
                    f"{card_def.name_jp} (コスト {card_def.cost})"
                )

        return choice

    def _get_affordable_options(self, player: Player) -> List[str]:
        """Return all options the player can currently afford."""
        options: List[str] = []

        for card_id, card_def in CARD_DEFS_BY_ID.items():
            if card_def.cost > player.coins:
                continue
            if (
                card_def.color == CardColor.PURPLE
                and player.count_establishments(card_id) >= 1
            ):
                continue
            options.append(card_id)

        for landmark_id, lm_def in LANDMARK_DEFS_BY_ID.items():
            if not player.landmarks.get(landmark_id, False) and lm_def.cost <= player.coins:
                options.append(f"landmark:{landmark_id}")

        return options

    def _get_game_state(self) -> GameState:
        return GameState(
            players=self.players,
            current_player_idx=self.current_player_idx,
            turn_number=self.turn_number,
        )
