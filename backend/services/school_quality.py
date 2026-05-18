"""School quality composite from OSM tags + OSM baseline ratings.

Returns a list of scored schools (up to 5 nearest), not just the nearest one.
The first entry (nearest school) is also returned in the legacy single-school
format for backward compatibility with the scoring engine.
"""
from __future__ import annotations


def _score_school(raw: dict, enriched_list: list[dict]) -> dict:
    dist = raw["distance_m"]

    # Match enriched entry by distance proximity
    google_rating = None
    for s in enriched_list:
        if abs(s.get("distance_m", 9999) - dist) < 20:
            google_rating = s.get("google_rating")
            break
    if google_rating is None and enriched_list:
        google_rating = enriched_list[0].get("google_rating")

    # OSM tags
    tags = raw.get("tags", {})
    operator_type = tags.get("operator:type", "")
    school_type = (
        "private"    if operator_type == "private" else
        "concertada" if operator_type in ("concertada", "religious") else
        "public"
    )
    language = (
        "english" if tags.get("language:en") == "yes" else
        "spanish" if tags.get("language:es") == "yes" and tags.get("language:ca") != "yes" else
        "catalan"
    )

    # Scoring
    dist_score   = max(0.0, 100.0 - dist / 5.0)
    type_bonus   = {"private": 80, "concertada": 70, "public": 60}[school_type]
    rating_score = ((google_rating - 1) / 4) * 100 if google_rating else 60.0
    composite    = round(dist_score * 0.40 + type_bonus * 0.20 + rating_score * 0.40, 1)

    return {
        "name":           raw.get("name", "School"),
        "distance_m":     dist,
        "school_type":    school_type,
        "language":       language,
        "google_rating":  google_rating,
        "composite_score": composite,
    }


def get_school_quality(poi_dict: dict, enriched_poi: dict) -> dict:
    """
    Returns:
      - Legacy single-school format (nearest_school_m, school_type, language,
        google_rating, composite_score) for the scoring engine.
      - Additional 'schools' list with up to 5 scored schools.
    """
    schools_raw      = poi_dict.get("school", [])
    schools_enriched = enriched_poi.get("school", [])

    if not schools_raw:
        return {
            "nearest_school_m": None,
            "school_type":      None,
            "language":         None,
            "google_rating":    None,
            "composite_score":  50.0,
            "schools":          [],
        }

    scored = [_score_school(s, schools_enriched) for s in schools_raw[:5]]
    nearest = scored[0]

    return {
        # Legacy fields (used by scoring engine)
        "nearest_school_m": nearest["distance_m"],
        "school_type":      nearest["school_type"],
        "language":         nearest["language"],
        "google_rating":    nearest["google_rating"],
        "composite_score":  nearest["composite_score"],
        # Full list
        "schools": scored,
    }
