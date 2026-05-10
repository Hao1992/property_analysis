"""Noise ecosystem: day vs night vs weekend noise estimate.

Key design principles:
- Floor level significantly reduces perceived street noise (7th floor ≈ 35% quieter than ground)
- Distance matters: weight each POI by (1 - distance/500) so a venue at 400m has 20% of the impact of one at 0m
- Type matters: nightclubs >> bars/pubs >> restaurants (cafes are irrelevant for noise)
- Bars are ALSO convenience amenities — counted positively in convenience.py, so we only penalise genuine noise risk here
- Missing data = neutral, not worst-case
"""

_FLOOR_BOOST_PER_LEVEL = 5   # each floor above ground adds ~5 pts to noise score
_MAX_FLOOR_BOOST = 40         # cap at 40 pts (roughly 8th floor and above)


def _distance_weight(distance_m: float, max_m: float = 500) -> float:
    """Linear falloff: weight 1.0 at 0m, 0.0 at max_m."""
    return max(0.0, 1.0 - distance_m / max_m)


def get_noise_ecosystem(poi_dict: dict, prop_data: dict) -> dict:
    restaurants_all = poi_dict.get("restaurant", [])

    # Floor level → noise discount
    floor = prop_data.get("floor") or 2  # default to 2nd floor if unknown
    floor_boost = min(_MAX_FLOOR_BOOST, max(0, (floor - 1) * _FLOOR_BOOST_PER_LEVEL))

    # ── Night noise ──────────────────────────────────────────────────────────
    # Only genuine nightlife venues count. Regular restaurants/cafes are not night noise.
    nightclubs = [p for p in restaurants_all if p.get("amenity") == "nightclub"]
    bars_pubs   = [p for p in restaurants_all if p.get("amenity") in ("bar", "pub")]

    # Distance-weighted severity (nightclub = 30 pts each, bar/pub = 10 pts each)
    nightclub_impact = sum(_distance_weight(p["distance_m"]) * 30 for p in nightclubs)
    bar_impact       = sum(_distance_weight(p["distance_m"]) * 10 for p in bars_pubs)

    # Cap total penalty at 90 so score never hits absolute zero from noise alone
    raw_night = max(10.0, 100.0 - min(nightclub_impact + bar_impact, 90.0))
    # Apply floor boost — higher floors experience less noise
    night_score = round(min(100.0, raw_night + floor_boost))

    # ── Day noise ────────────────────────────────────────────────────────────
    # Construction risk is the main uncontrollable day-noise factor.
    # Bus stops are NOT a noise risk — they signal transit quality (positive).
    year_built = prop_data.get("year_built") or 1980
    age = 2025 - year_built
    construction_risk = "high" if age > 60 else "medium" if age > 30 else "low"
    construction_penalty = {"high": 15, "medium": 8, "low": 0}[construction_risk]

    # Heavy-traffic roads: we don't have this from OSM directly, use hospital proximity as a
    # weak ambulance-siren proxy (very rough — acknowledged limitation)
    hospitals_close = len([p for p in poi_dict.get("hospital", []) if p["distance_m"] <= 300])
    raw_day = max(20.0, 100.0 - construction_penalty - hospitals_close * 5)
    day_score = round(min(100.0, raw_day + floor_boost * 0.6))  # floors help less for day noise

    # ── Weekend noise ────────────────────────────────────────────────────────
    weekend_score = round(night_score * 0.60 + day_score * 0.40)

    return {
        "day_noise_score":     day_score,
        "night_noise_score":   night_score,
        "weekend_noise_score": weekend_score,
        "bars_clubs_500m":     len(bars_pubs) + len(nightclubs),
        "nightclubs_500m":     len(nightclubs),
        "floor_boost_applied": floor_boost,
        "construction_risk":   construction_risk,
    }
