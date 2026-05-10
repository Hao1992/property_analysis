"""Intangible neighbourhood value — what other property sites don't measure.

Three signals (local_commerce removed vs v1):
  cultural_density  — libraries, theatres, arts/community centres within 500 m
  local_market      — distance to a traditional covered market (mercat)
  green_urban_quality — park proximity (sole park signal; park_access from
                        Convenience merged here to eliminate double-counting)

local_commerce was removed: OSM brand tag coverage is too sparse and
inconsistent. A chain restaurant without a brand= tag appears "independent",
producing systematic false-positive scores for some neighbourhoods.

green_urban_quality weight raised from 0.15 → 0.35 to reflect its expanded
role as the only park dimension in the composite.
"""
from __future__ import annotations


def score_intangible(poi_dict: dict, enriched_poi: dict) -> dict[str, float | None]:
    sub: dict[str, float | None] = {}

    # ── Cultural density ─────────────────────────────────────────────────────
    cultural = (
        poi_dict.get("library", [])
        + poi_dict.get("cultural_centre", [])
        + poi_dict.get("theatre", [])
    )
    n = len(cultural)
    # Logarithmic saturation: 1 venue ≈ 33 pts, 2 ≈ 50, 4 ≈ 67, 8+ ≈ 89
    sub["cultural_density"] = round(min(100.0, 100.0 * (1 - 1 / (1 + n / 2)))) if n else 0

    # ── Traditional market proximity ─────────────────────────────────────────
    markets = poi_dict.get("marketplace", [])
    if markets:
        nearest_m = markets[0]["distance_m"]
        # 0 m → 100, 400 m → 50, 800 m → 0  (linear)
        sub["local_market"] = round(max(0.0, 100.0 - nearest_m / 8.0))
    else:
        sub["local_market"] = None  # OSM gap — not the same as "no market"

    # ── Green urban quality (sole park signal) ───────────────────────────────
    # Absorbs the former Convenience.park_access to avoid double-counting.
    # Concave decay: 0 m → 100, 250 m → 53, 500 m → 0
    parks = poi_dict.get("park", [])
    if parks:
        d = parks[0]["distance_m"]
        sub["green_urban_quality"] = round(max(0.0, 100.0 * (1.0 - d / 500.0) ** 1.5))
    else:
        sub["green_urban_quality"] = 0  # measurable absence of green space

    return sub
