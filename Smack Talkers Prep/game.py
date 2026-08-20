"""Pure game rules for the Smack Talkers Draft simulator."""

from __future__ import annotations

import random
from collections import Counter

SIGNS = ("MIN", "MAX", "ABS", "SUM")
POWER_UPS = (
    "Half your value",
    "Subtract a random 10-dice roll",
    "Minimum of two new cards",
    "Straight up a 10-point card",
    "Redo to use later",
)


def apply_sign(current: int, new: int, sign: str) -> int:
    """Apply one of the four Sign & Card operators."""
    if sign == "MIN":
        return min(current, new)
    if sign == "MAX":
        return max(current, new)
    if sign == "ABS":
        return abs(current - new)
    if sign == "SUM":
        return current + new
    raise ValueError(f"Unknown sign: {sign}")


def blackjack_value(cards: list[int]) -> int:
    """Return a blackjack hand value; aces arrive as 11 and soften to 1."""
    total = sum(cards)
    aces = cards.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def blackjack_is_soft(cards: list[int]) -> bool:
    """Whether at least one ace is still valued as 11."""
    return 11 in cards and sum(cards) <= 21


def dealer_play(rng: random.Random, cards: list[int] | None = None) -> list[int]:
    cards = list(cards) if cards else [draw_blackjack_card(rng), draw_blackjack_card(rng)]
    while blackjack_value(cards) < 17 or (blackjack_value(cards) == 17 and blackjack_is_soft(cards)):
        cards.append(draw_blackjack_card(rng))
    return cards


def apply_powerup(score: float, index: int, bid: int, rng: random.Random) -> tuple[float, str]:
    """Add the winning bid, apply a power-up, and return an auditable description."""
    score += bid
    if index == 0:
        return score / 2, f"added bid {bid}, then halved the score"
    if index == 1:
        rolls = [rng.randint(1, 6) for _ in range(10)]
        total = sum(rolls)
        return score - total, f"added bid {bid}, rolled {rolls} = {total}, then subtracted {total}"
    if index == 2:
        cards = [rng.randint(1, 100), rng.randint(1, 100)]
        return min(score, *cards), f"added bid {bid}, drew {cards}, then took the minimum"
    if index == 3:
        return 10 + bid, f"score became 10 plus winning bid {bid}"
    return score, f"added bid {bid} and banked one redo"


def build_hidden_players(seed: int, count: int = 11) -> tuple[list[dict], str]:
    """Create hidden opponents through halftime and reserve one balanced sign for the user."""
    rng = random.Random(seed + 73_001)
    signs = [sign for sign in SIGNS for _ in range(3)]
    rng.shuffle(signs)
    user_sign = signs.pop()
    players = []
    for seat in range(2, count + 2):
        name = f"Player {seat}"
        score = rng.randint(21, 100)
        path = [{"stage": "Pre-Game", "detail": f"drew {score}", "score": score}]
        if score > 50 or rng.random() < 0.18:
            score = rng.randint(1, 100)
            q1 = f"drew a new {score}"
        else:
            q1 = "kept"
        path.append({"stage": "First Quarter", "detail": q1, "score": score})
        assigned_sign = signs.pop()
        if rng.random() < 0.78:
            card = rng.randint(1, 100)
            before = score
            score = apply_sign(score, card, assigned_sign)
            q2 = f"drew {assigned_sign} + {card}: {before} → {score}"
        else:
            q2 = f"kept (assigned {assigned_sign} remained unused)"
        path.append({"stage": "Second Quarter", "detail": q2, "score": score})
        bids = {power: rng.randint(0, 30) for power in POWER_UPS}
        players.append({"name": name, "score": score, "path": path, "bids": bids, "powerups": []})
    return players, user_sign


def finish_hidden_players(
    players: list[dict],
    user_bids: dict[str, int],
    rng: random.Random,
    winners: dict[str, str] | None = None,
) -> list[dict]:
    """Resolve shared auctions, then finish each opponent's private Q4 and OT path."""
    for index, power in enumerate(POWER_UPS):
        entries = [("You", user_bids[power])] + [(p["name"], p["bids"][power]) for p in players]
        high = max(bid for _, bid in entries)
        tied = [name for name, bid in entries if bid == high]
        winner = winners[power] if winners else rng.choice(tied)
        for player in players:
            if player["name"] == winner and high > 0:
                player["score"], detail = apply_powerup(player["score"], index, high, rng)
                player["powerups"].append(power)
                player["path"].append({"stage": "Third Quarter", "detail": f"won {power}: {detail}", "score": player["score"]})
    for player in players:
        if not any(event["stage"] == "Third Quarter" for event in player["path"]):
            player["path"].append({"stage": "Third Quarter", "detail": "won no auctions", "score": player["score"]})
        dice_count = rng.randint(1, 6)
        multiplier = rng.randint(1, 5)
        rolls = [rng.randint(1, 6) for _ in range(dice_count)]
        redo_note = ""
        if "Redo to use later" in player["powerups"] and dice_delta(rolls) > 0:
            first_rolls = rolls
            rolls = [rng.randint(1, 6) for _ in range(dice_count)]
            player["powerups"].remove("Redo to use later")
            redo_note = f"; used redo on {first_rolls}, rerolled "
        player["score"] = fourth_quarter_result(player["score"], rolls, multiplier)
        player["path"].append({"stage": "Fourth Quarter", "detail": f"{redo_note}rolled {rolls}; {dice_delta(rolls):+d} × {multiplier}", "score": player["score"], "dice": rolls, "quantity": dice_count, "multiplier": multiplier, "adjustment": dice_delta(rolls) * multiplier, "redo_used": bool(redo_note)})
        if rng.random() < 0.55:
            die = rng.randint(1, 6)
            redo_note = ""
            if "Redo to use later" in player["powerups"] and die > 1:
                first_die = die
                die = rng.randint(1, 6)
                player["powerups"].remove("Redo to use later")
                redo_note = f"used redo on {first_die}, then "
            player["score"] = overtime_result(player["score"], die)
            detail = f"{redo_note}played and rolled {die}"
        else:
            detail = "kept"
        player["path"].append({"stage": "Overtime", "detail": detail, "score": player["score"]})
    return players


def draw_blackjack_card(rng: random.Random) -> int:
    return rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11])


def blackjack_result(player: list[int], dealer: list[int]) -> bool:
    """Compatibility helper: true only for a win."""
    return blackjack_outcome(player, dealer) == "win"


def blackjack_outcome(player: list[int], dealer: list[int]) -> str:
    p, d = blackjack_value(player), blackjack_value(dealer)
    if p > 21:
        return "loss"
    if d > 21 or p > d:
        return "win"
    if p == d:
        return "push"
    return "loss"


def blackjack_score(score: float, hand: list[int], outcome: str | bool) -> float:
    """Natural blackjack divides by 3, other wins divide by 2, losses double."""
    if outcome == "push":
        return score
    won = outcome is True or outcome == "win"
    if not won:
        return score * 2
    return score / 3 if len(hand) == 2 and blackjack_value(hand) == 21 else score / 2


def dice_delta(rolls: list[int]) -> int:
    """Unique faces subtract once; repeated faces add once per occurrence."""
    counts = Counter(rolls)
    return sum(face * count if count >= 2 else -face for face, count in counts.items())


def fourth_quarter_result(current: float, rolls: list[int], multiplier: int) -> float:
    return current + dice_delta(rolls) * multiplier


def overtime_result(current: float, die: int) -> float:
    if not 1 <= die <= 6:
        raise ValueError("Die must be from 1 to 6")
    return 1 if die == 1 else current * die


def simulate_game(rng: random.Random, sign: str | None = None) -> float:
    """Fast baseline bot for the Simulation Lab (no auction bidding)."""
    score = rng.randint(21, 100)
    # Q1: redraw only when above the expected draw (50.5).
    if score > 50:
        score = rng.randint(1, 100)
    sign = sign or rng.choice(SIGNS)
    score = apply_sign(score, rng.randint(1, 100), sign)
    player = [draw_blackjack_card(rng), draw_blackjack_card(rng)]
    while blackjack_value(player) < 17:
        player.append(draw_blackjack_card(rng))
    dealer = dealer_play(rng)
    outcome = blackjack_outcome(player, dealer)
    score = blackjack_score(score, player, outcome)
    rolls = [rng.randint(1, 6) for _ in range(rng.randint(1, 6))]
    score = fourth_quarter_result(score, rolls, rng.randint(1, 5))
    score = overtime_result(score, rng.randint(1, 6))
    return score
