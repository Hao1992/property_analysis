"""School quality composite from OSM tags + Google Places ratings.

No additional API calls: uses POI data already fetched by overpass.py
and Google ratings already fetched by google_places.py.
"""


def get_school_quality(poi_dict: dict, enriched_poi: dict) -> dict:
    schools_raw = poi_dict.get("school", [])
    schools_enriched = enriched_poi.get("school", [])

    if not schools_raw:
        return {
            "nearest_school_m": None,
            "school_type": None,
            "language": None,
            "google_rating": None,
            "composite_score": 50.0,
        }

    nearest_raw = schools_raw[0]
    nearest_m = nearest_raw["distance_m"]

    # Match enriched entry for the nearest school
    google_rating = None
    for s in schools_enriched:
        if abs(s.get("distance_m", 9999) - nearest_m) < 20:
            google_rating = s.get("google_rating")
            break
    if google_rating is None and schools_enriched:
        google_rating = schools_enriched[0].get("google_rating")

    # OSM tags for type and language
    tags = nearest_raw.get("tags", {})
    operator_type = tags.get("operator:type", "")
    school_type = (
        "private"    if operator_type == "private" else
        "concertada" if operator_type in ("concertada", "religious") else
        "public"
    )
    language = (
        "english" if tags.get("language:en") == "yes" else
        "spanish" if tags.get("language:es") == "yes" and tags.get("language:ca") != "yes" else
        "catalan"   # BCN default
    )

    # Scoring
    dist_score = max(0.0, 100.0 - nearest_m / 5.0)     # full score ≤500m
    type_bonus = {"private": 80, "concertada": 70, "public": 60}[school_type]
    rating_score = ((google_rating - 1) / 4) * 100 if google_rating else 60.0

    composite = dist_score * 0.40 + type_bonus * 0.20 + rating_score * 0.40

    return {
        "nearest_school_m": nearest_m,
        "school_type": school_type,
        "language": language,
        "google_rating": google_rating,
        "composite_score": round(composite, 1),
    }
