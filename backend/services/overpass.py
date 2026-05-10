import httpx
import math
import os

OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

CATEGORY_MAP = {
    "supermarket":    {"amenity": ["supermarket"], "shop": ["supermarket", "convenience", "grocery"]},
    "restaurant":     {"amenity": ["restaurant", "cafe", "bar", "pub", "nightclub"]},
    "pharmacy":       {"amenity": ["pharmacy"]},
    "school":         {"amenity": ["school", "kindergarten"]},
    "park":           {"leisure": ["park", "garden"]},
    "bus_stop":       {"highway": ["bus_stop"]},
    "metro":          {"railway": ["station", "subway_entrance"], "station": ["subway"]},
    "hospital":       {"amenity": ["hospital", "clinic"]},
    # Intangible dimension sources
    "library":        {"amenity": ["library"]},
    "cultural_centre":{"amenity": ["arts_centre", "cultural_centre", "community_centre"]},
    "theatre":        {"amenity": ["theatre", "cinema"]},
    "marketplace":    {"amenity": ["marketplace"]},
}

# Used only for the amenity_density sub-score in Convenience.
# School is scored separately in Liveability; parking removed (not a convenience amenity).
CATEGORY_WEIGHTS = {
    "supermarket": 0.30,
    "restaurant":  0.22,
    "pharmacy":    0.18,
    "hospital":    0.12,
    "bus_stop":    0.08,
    "metro":       0.10,
}


async def fetch_pois(lat: float, lng: float, radius_m: int = 500) -> dict:
    """Returns dict of category -> list of {name, lat, lng, distance_m, osm_id, routes} sorted by distance."""
    # Query both node and way elements (many shops/restaurants in BCN are mapped as buildings/ways)
    filters = []
    for cat, tags in CATEGORY_MAP.items():
        for tag_key, tag_vals in tags.items():
            for val in tag_vals:
                filters.append(f'node["{tag_key}"="{val}"](around:{radius_m},{lat},{lng});')
                filters.append(f'way["{tag_key}"="{val}"](around:{radius_m},{lat},{lng});')

    query = f"""
[out:json][timeout:30];
({chr(10).join(filters)});
out center tags;
"""
    _HEADERS = {"User-Agent": "PropertyAnalyzer/2.0 (contact: dev@propertyanalyzer.es)"}
    try:
        async with httpx.AsyncClient(timeout=35, headers=_HEADERS) as client:
            r = await client.post(OVERPASS_URL, data={"data": query})
            r.raise_for_status()
            elements = r.json().get("elements", [])
    except Exception:
        elements = []

    # Also fetch transit route numbers for bus stops in the area
    transit_routes = await _fetch_transit_routes(lat, lng, radius_m)

    result: dict[str, list] = {cat: [] for cat in CATEGORY_MAP}
    seen = set()  # deduplicate by name+distance

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("brand") or tags.get("operator") or "Unnamed"
        # ways have a "center" key; nodes have lat/lon directly
        center = el.get("center", {})
        el_lat = center.get("lat") or el.get("lat", lat)
        el_lng = center.get("lon") or el.get("lon", lng)
        dist = round(haversine(lat, lng, el_lat, el_lng))
        category = classify_element(tags)
        if not category:
            continue

        dedup_key = (category, name, dist)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Collect route_ref lines for transit stops
        routes: list[str] = []
        if category in ("bus_stop", "metro"):
            route_ref = tags.get("route_ref", "")
            if route_ref:
                # BCN OSM uses spaces, semicolons, or commas as separators
                import re
                routes = [r.strip() for r in re.split(r'[;,\s]+', route_ref) if r.strip()]
            # Also check against fetched route relations
            stop_name_lower = name.lower()
            for route_name, stops_in_route in transit_routes.items():
                if any(stop_name_lower in s.lower() for s in stops_in_route):
                    if route_name not in routes:
                        routes.append(route_name)

        result[category].append({
            "name": name,
            "lat": el_lat,
            "lng": el_lng,
            "distance_m": dist,
            "osm_id": el.get("id"),
            "routes": routes,
            "amenity": tags.get("amenity", ""),
            "tags": tags,   # kept for school_quality.py OSM tag inspection
        })

    for cat in result:
        result[cat].sort(key=lambda x: x["distance_m"])

    return result


async def _fetch_transit_routes(lat: float, lng: float, radius_m: int) -> dict[str, list[str]]:
    """Returns {route_ref: [stop_name, ...]} for bus/metro routes passing through the area."""
    query = f"""
[out:json][timeout:20];
relation["type"="route"]["route"~"^(bus|subway|tram|light_rail)$"](around:{radius_m},{lat},{lng});
out tags;
"""
    _HEADERS = {"User-Agent": "PropertyAnalyzer/2.0 (contact: dev@propertyanalyzer.es)"}
    try:
        async with httpx.AsyncClient(timeout=25, headers=_HEADERS) as client:
            r = await client.post(OVERPASS_URL, data={"data": query})
            r.raise_for_status()
            relations = r.json().get("elements", [])
    except Exception:
        return {}

    routes: dict[str, list[str]] = {}
    for rel in relations:
        tags = rel.get("tags", {})
        ref = tags.get("ref") or tags.get("name", "")
        if ref:
            routes[ref] = []
    return routes


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def classify_element(tags: dict) -> str | None:
    amenity = tags.get("amenity", "")
    leisure  = tags.get("leisure", "")
    highway  = tags.get("highway", "")
    shop     = tags.get("shop", "")
    railway  = tags.get("railway", "")
    station  = tags.get("station", "")

    if amenity == "supermarket" or shop in ["supermarket", "convenience", "grocery"]: return "supermarket"
    if amenity in ["restaurant", "cafe", "bar", "pub", "nightclub"]: return "restaurant"
    if amenity == "pharmacy": return "pharmacy"
    if amenity in ["school", "kindergarten"]: return "school"
    if amenity in ["hospital", "clinic"]: return "hospital"
    if leisure in ["park", "garden"]: return "park"
    if highway == "bus_stop": return "bus_stop"
    if railway in ["station", "subway_entrance"] or station == "subway": return "metro"
    if amenity == "library": return "library"
    if amenity in ["arts_centre", "cultural_centre", "community_centre"]: return "cultural_centre"
    if amenity in ["theatre", "cinema"]: return "theatre"
    if amenity == "marketplace": return "marketplace"
    return None
