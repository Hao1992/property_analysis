"""OSM baseline ratings — drop-in replacement for Google Places enrichment.

Returns the same {google_rating, google_reviews, is_open} interface so all
downstream scoring code (school_quality.py, etc.) works unchanged.

google_rating values are Google-scale equivalents (1–5) derived from
OSM amenity-type quality priors. google_reviews and is_open are always None.
"""

# Quality priors on 0–10 scale, per OSM amenity/category type.
# Overpass category names (metro, gym, etc.) are included so they work as
# the category-level fallback in _baseline_rating without a separate dict.
# Sources: Barcelona median Google ratings by category (2024 survey) + editorial judgment.
_OSM_QUALITY: dict[str, float] = {
    # Education
    "school":           6.5,
    "kindergarten":     6.5,
    "university":       7.5,
    "college":          7.0,
    # Healthcare
    "hospital":         7.0,
    "clinic":           6.8,
    "pharmacy":         7.2,
    "dentist":          7.0,
    "doctors":          6.8,
    # Food & drink
    "restaurant":       7.0,
    "cafe":             7.2,
    "bar":              6.8,
    "pub":              6.8,
    "fast_food":        6.0,
    "food_court":       6.0,
    "nightclub":        6.5,
    # Retail & daily needs
    "supermarket":      7.0,
    "convenience":      6.2,
    "grocery":          6.5,
    # Transport (OSM tag names + overpass category names)
    "bus_stop":         6.5,
    "subway_entrance":  8.0,
    "station":          7.5,
    "metro":            8.0,
    # Green space & leisure (OSM tag names + overpass category names)
    "park":             8.0,
    "garden":           7.5,
    "fitness_centre":   7.0,
    "gym":              7.0,
    "sports_centre":    7.0,
    # Culture & community (OSM tag names + overpass category names)
    "library":          7.5,
    "theatre":          7.5,
    "cinema":           7.0,
    "arts_centre":      7.5,
    "cultural_centre":  7.0,
    "community_centre": 6.5,
    "marketplace":      7.5,
}

_DEFAULT_QUALITY = 6.5


def _osm_to_google_scale(osm_score: float) -> float:
    """Map 0–10 OSM quality score to Google 1–5 scale."""
    return round(1.0 + (osm_score / 10.0) * 4.0, 1)


def _baseline_rating(poi: dict, category: str) -> float:
    """Return Google-scale baseline rating for a single POI."""
    tags = poi.get("tags", {})
    amenity = poi.get("amenity", "") or tags.get("amenity", "")
    lookup_key = amenity or tags.get("shop", "") or tags.get("leisure", "") or tags.get("railway", "")

    osm_score = _OSM_QUALITY.get(lookup_key)
    if osm_score is None:
        osm_score = _OSM_QUALITY.get(category)
    if osm_score is None:
        osm_score = _DEFAULT_QUALITY
    return _osm_to_google_scale(osm_score)


async def enrich_with_ratings(poi_dict: dict) -> dict:
    """
    Takes Overpass POI dict, returns same structure with OSM baseline
    ratings in google_rating, google_reviews=None, is_open=None.

    Drop-in replacement for the former Google Places implementation.
    Downstream scoring code (school_quality.py) is unchanged.
    """
    result = {}
    for category, pois in poi_dict.items():
        if not isinstance(pois, list):
            result[category] = pois  # preserve non-list metadata entries as-is
            continue
        result[category] = [
            {
                **poi,
                "google_rating": _baseline_rating(poi, category),
                "google_reviews": None,
                "is_open": None,
            }
            for poi in pois
        ]
    return result
