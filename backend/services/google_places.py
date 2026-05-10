import httpx
import math
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
TOP_N_PER_CATEGORY = 3


async def enrich_with_ratings(poi_dict: dict) -> dict:
    """
    Takes Overpass POI dict, returns same structure enriched with
    {google_rating, google_reviews, is_open} for top N per category.
    If no API key is configured, returns poi_dict unchanged.
    """
    if not GOOGLE_API_KEY:
        # No key — return data as-is with null ratings
        return {
            cat: [{**poi, "google_rating": None, "google_reviews": None, "is_open": None}
                  for poi in pois]
            for cat, pois in poi_dict.items()
        }

    enriched = {}
    for category, pois in poi_dict.items():
        top = pois[:TOP_N_PER_CATEGORY]
        enriched_top = []
        for poi in top:
            details = await get_place_details(poi["name"], poi["lat"], poi["lng"])
            enriched_top.append({**poi, **details})
        enriched[category] = enriched_top + pois[TOP_N_PER_CATEGORY:]
    return enriched


async def get_place_details(name: str, lat: float, lng: float) -> dict:
    place_id = await find_place_id(name, lat, lng)
    if not place_id:
        return {"google_rating": None, "google_reviews": None, "is_open": None}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={
                    "place_id": place_id,
                    "fields": "rating,user_ratings_total,opening_hours/open_now",
                    "key": GOOGLE_API_KEY
                }
            )
            result = r.json().get("result", {})
    except Exception:
        return {"google_rating": None, "google_reviews": None, "is_open": None}

    return {
        "google_rating": result.get("rating"),
        "google_reviews": result.get("user_ratings_total"),
        "is_open": result.get("opening_hours", {}).get("open_now")
    }


async def find_place_id(name: str, lat: float, lng: float) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
                params={
                    "input": name,
                    "inputtype": "textquery",
                    "locationbias": f"circle:100@{lat},{lng}",
                    "fields": "place_id,name,geometry",
                    "key": GOOGLE_API_KEY
                }
            )
            candidates = r.json().get("candidates", [])
    except Exception:
        return None

    if not candidates:
        return None

    candidate = candidates[0]
    loc = candidate.get("geometry", {}).get("location", {})
    c_lat = loc.get("lat", lat)
    c_lng = loc.get("lng", lng)
    dist = _haversine(lat, lng, c_lat, c_lng)
    if dist > 80:
        return None

    return candidate.get("place_id")


def _haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lng2 - lng1) / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
