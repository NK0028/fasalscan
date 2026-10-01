"""Turns raw detections + weather into a grade, a shelf-life estimate and an action."""

from collections import Counter

# Rough days until noticeable quality loss at ~20°C ambient storage (no cold chain).
BASE_SHELF_DAYS = {
    "apple": 12, "pear": 7, "orange": 12, "lemon": 14, "banana": 5, "peach": 4,
    "apricot": 4, "plum": 5, "mango": 6, "persimmon": 7, "tomato": 6, "guava": 4,
    "pomegranate": 20, "grape": 4, "strawberry": 2,
}
DEFAULT_SHELF_DAYS = 6

GRADES = [  # (max reject %, grade, label)
    (5, "A", "Premium"),
    (15, "B", "Good"),
    (35, "C", "Fair"),
    (100, "D", "Process only"),
]


def _grade(reject_pct: float) -> tuple[str, str]:
    for limit, grade, label in GRADES:
        if reject_pct <= limit:
            return grade, label
    return "D", "Process only"


def _shelf_life(fruit: str, temp_c: float, humidity: float, reject_ratio: float) -> float:
    base = BASE_SHELF_DAYS.get(fruit, DEFAULT_SHELF_DAYS)
    temp_factor = min(2.5, max(0.35, 2 ** ((20 - temp_c) / 10)))  # Q10 ≈ 2
    humidity_factor = 0.85 if humidity < 35 else 1.0
    rot_factor = (1 - reject_ratio) ** 1.5
    if reject_ratio > 0:
        rot_factor *= 0.85  # mould spreads to neighbours in a closed crate
    return max(0.5, round(base * temp_factor * humidity_factor * rot_factor * 2) / 2)


def _action(total: int, reject_pct: float, days: float, grade: str) -> str:
    if total == 0:
        return "none"
    if reject_pct >= 35:
        return "process"
    if days < 2:
        return "sell_now"
    if reject_pct >= 10:
        return "sort_first"
    if grade == "A" and days >= 5:
        return "hold"
    return "sell_soon"


def _range(days: float) -> list[float]:
    """Whole days once the estimate is a few days long, halves below that."""
    lo, hi = max(0.5, days * 0.7), days * 1.3
    if days >= 3:
        return [float(round(lo)), float(round(hi))]
    return [round(lo * 2) / 2, round(hi * 2) / 2]


def analyse(detections: list[dict], weather: dict) -> dict:
    total = len(detections)
    rotten = sum(1 for d in detections if d["state"] == "rotten")
    fresh = total - rotten
    reject_ratio = rotten / total if total else 0.0
    reject_pct = round(reject_ratio * 100, 1)

    per_fruit: dict[str, Counter] = {}
    for d in detections:
        per_fruit.setdefault(d["fruit"], Counter())[d["state"]] += 1
    breakdown = sorted(
        ({"fruit": f, "fresh": c["fresh"], "rotten": c["rotten"]} for f, c in per_fruit.items()),
        key=lambda b: b["fresh"] + b["rotten"],
        reverse=True,
    )
    dominant = breakdown[0]["fruit"] if breakdown else "unknown"

    if total:
        grade, grade_label = _grade(reject_pct)
        temp = weather.get("outlook_c", weather["temp_c"])
        days = _shelf_life(dominant, temp, weather["humidity"], reject_ratio)
    else:
        grade, grade_label, days = "-", "No fruit found", 0.0

    return {
        "total": total,
        "fresh": fresh,
        "rotten": rotten,
        "reject_pct": reject_pct,
        "grade": grade,
        "grade_label": grade_label,
        "fruit": dominant,
        "days_left": days,
        "days_range": _range(days) if total else [0, 0],
        "action": _action(total, reject_pct, days, grade),
        "breakdown": breakdown,
        "detections": detections,
    }
