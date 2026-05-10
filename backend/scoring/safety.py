"""Safety dimension: passes through the four crime indices from Open Data BCN.

The raw indices come pre-normalised to 0–100 from the data layer, so this
module is intentionally thin.  Vehicle-crime weight is profile-sensitive
(car owners care more) — that adjustment happens in the engine via sub_weights.
"""
from __future__ import annotations


def score_safety(safety_data: dict) -> dict[str, float | None]:
    def _get(key: str) -> float | None:
        v = safety_data.get(key)
        return float(v) if v is not None else None

    return {
        "theft_rate":    _get("theft_rate_index"),
        "vehicle_crime": _get("vehicle_crime_index"),
        "vandalism":     _get("vandalism_index"),
        "night_safety":  _get("night_safety_index"),
    }
