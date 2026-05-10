"""Convenience dimension: transit connectivity, amenity density, Google quality.

park_access removed from this dimension — it is now the sole park signal in
Intangible.green_urban_quality, eliminating the double-count that previously
inflated the park signal across two dimensions.

Transit uses route COUNT (lines served), not just distance: a metro station
with 3 lines is fundamentally more connected than one with 1.
"""
from __future__ import annotations

import math

from services.overpass import CATEGORY_WEIGHTS


def score_convenience(poi_dict: dict, enriched: dict) -> dict[str, float | None]:
    sub: dict[str, float | None] = {}

    # ── Transit proximity & connectivity ─────────────────────────────────────
    metro_stops = poi_dict.get("metro", [])[:5]
    bus_stops   = poi_dict.get("bus_stop", [])[:8]

    metro_score = 0.0
    if metro_stops:
        nearest_m = metro_stops[0]["distance_m"]
        # Proximity: 0 m → 100, 500 m → 0 (industry walkability standard)
        proximity = max(0.0, 100.0 - nearest_m / 5.0)
        # Line count bonus: each metro line adds connectivity
        all_metro_routes: set[str] = set()
        for s in metro_stops:
            all_metro_routes.update(s.get("routes", []))
        line_bonus = min(30.0, len(all_metro_routes) * 10.0)
        metro_score = min(100.0, proximity * 0.75 + line_bonus * 0.25)

    bus_score = 0.0
    if bus_stops:
        nearest_m = bus_stops[0]["distance_m"]
        # Proximity of nearest stop (0 m → 100, 300 m → 0)
        proximity = max(0.0, 100.0 - nearest_m / 3.0)
        # Distinct routes from all nearby stops (connectivity diversity)
        all_bus_routes: set[str] = set()
        for s in bus_stops:
            all_bus_routes.update(s.get("routes", []))
        route_bonus = min(40.0, len(all_bus_routes) * 5.0)
        bus_score = min(100.0, proximity * 0.65 + route_bonus * 0.35)

    sub["transit_proximity"] = round(metro_score * 0.65 + bus_score * 0.35)

    # ── Amenity density ──────────────────────────────────────────────────────
    # School deliberately excluded — scored in Liveability with quality focus.
    density_score = 0.0
    for cat, weight in CATEGORY_WEIGHTS.items():
        pois = poi_dict.get(cat, [])
        # Hospital/pharmacy: half-saturation at 2 (rare enough that 1 is meaningful)
        half_sat = 2 if cat in ("hospital", "pharmacy") else 4
        cat_score = _sat(len(pois), half_sat)
        density_score += weight * cat_score
    sub["amenity_density"] = round(density_score)

    # ── Google quality ───────────────────────────────────────────────────────
    sub["google_quality"] = _google_quality(enriched)

    return sub


def _sat(count: int, half_sat: int = 4) -> float:
    """Logarithmic saturation — diminishing returns, avoids rewarding excess density."""
    if count == 0:
        return 0.0
    return min(100.0, 100.0 * (1 - 1 / (1 + count / half_sat)))


def _google_quality(enriched: dict) -> float | None:
    scores = []
    for cat, weight in CATEGORY_WEIGHTS.items():
        items = enriched.get(cat, [])[:3]
        rated = [i for i in items if i.get("google_rating")]
        if not rated:
            continue
        for item in rated:
            rating  = item["google_rating"]
            reviews = item.get("google_reviews") or 0
            # Bayesian confidence: needs ~30 reviews for full trust
            conf = min(1.0, math.log1p(reviews) / math.log1p(30))
            scores.append(weight * (rating / 5.0) * conf)
    if not scores:
        return None
    return round(min(100.0, sum(scores) * 100))
