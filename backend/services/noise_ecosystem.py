"""Noise ecosystem: day, night, and weekend noise estimates.

Data confidence levels:
- Day score: MEDIUM — based on OSM road classification (motorway/trunk/primary).
  BCN road network is well-mapped in OSM. Score is directionally reliable.
- Night score: MEDIUM — based on OSM bar/nightclub tags. Coverage is good but
  incomplete; some venues may be untagged. Score is directionally correct.
- Weekend score: derived from both day and night.
- construction_risk: building attribute (age-based), NOT a noise score.
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

    # ── Day noise (road traffic) ─────────────────────────────────────────────
    # _road_noise_score comes from overpass._fetch_road_noise() — OSM highway classification.
    raw_day = poi_dict.get("_road_noise_score", 50)  # 50 = neutral fallback
    # Floors help somewhat with traffic noise but less than nightlife
    day_score = round(min(100.0, raw_day + floor_boost * 0.5))

    # ── Night noise (nightlife POIs) ─────────────────────────────────────────
    nightclubs = [p for p in restaurants_all if p.get("amenity") == "nightclub"]
    bars_pubs   = [p for p in restaurants_all if p.get("amenity") in ("bar", "pub")]

    nightclub_impact = sum(_distance_weight(p["distance_m"]) * 30 for p in nightclubs)
    bar_impact       = sum(_distance_weight(p["distance_m"]) * 10 for p in bars_pubs)

    raw_night = max(10.0, 100.0 - min(nightclub_impact + bar_impact, 90.0))
    night_score = round(min(100.0, raw_night + floor_boost))

    # ── Weekend: average of day and night pressure ───────────────────────────
    weekend_score = round(night_score * 0.65 + day_score * 0.35)

    # ── Building age → construction risk label (NOT a noise score) ───────────
    year_built = prop_data.get("year_built") or 1980
    age = 2025 - year_built
    construction_risk = "high" if age > 60 else "medium" if age > 30 else "low"

    return {
        "day_noise_score":     day_score,
        "night_noise_score":   night_score,
        "weekend_noise_score": weekend_score,
        "bars_clubs_500m":     len(bars_pubs) + len(nightclubs),
        "nightclubs_500m":     len(nightclubs),
        "floor_boost_applied": floor_boost,
        "construction_risk":   construction_risk,
        "night_data_note":     "osm_poi",
    }
