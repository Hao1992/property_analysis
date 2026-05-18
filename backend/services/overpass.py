import httpx
import math
import os

OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

# Barcelona metro (TMB) and FGC station → line mapping.
# OSM route_ref tags are often absent for FGC/Tramvia stations; this fills the gap.
_BCN_TRANSIT_LINES: dict[str, list[str]] = {
    # TMB Metro L1 (red)
    "marina":          ["L1"], "clot":         ["L1"], "glòries":       ["L1"],
    "arc de triomf":   ["L1"], "urquinaona":   ["L1"], "catalunya":     ["L1","L3"],
    "universitat":     ["L1","L2"], "hospital clínic": ["L5"], "espanya":  ["L1","L3"],
    # TMB Metro L2 (purple)
    "sant antoni":     ["L2"], "paral·lel":    ["L2","L3"], "bogatell":  ["L4"],
    "la pau":          ["L2","L4"], "verneda":  ["L2"],
    # TMB Metro L3 (green)
    "lesseps":         ["L3"], "fontana":      ["L3"], "diagonal":      ["L3","L5"],
    "passeig de gràcia": ["L2","L3","L4"], "liceu": ["L3"], "drassanes": ["L3"],
    "barceloneta":     ["L4"], "ciutadella / vila olímpica": ["L4"],
    "vallcarca":       ["L3"], "penitents":    ["L3"], "vall d'hebron": ["L3"],
    "montbau":         ["L3"], "mundet":       ["L3"], "canyelles":     ["L3"],
    "roquetes":        ["L3"], "trinitat nova": ["L3","L4"],
    # TMB Metro L4 (yellow)
    "jaume i":         ["L4"], "barceloneta":  ["L4"], "poblenou":      ["L4"],
    "selva de mar":    ["L4"], "el maresme / fòrum": ["L4"],
    # TMB Metro L5 (blue)
    "collblanc":       ["L5","L9S"], "badal":  ["L5"], "entença":       ["L5"],
    "hospital de bellvitge": ["L1"], "pubilla cases": ["L5"],
    # FGC Vallvidrera / Tibidabo line (L7 / Vallvidrera line)
    # Stations with station=subway in OSM — these appear correctly
    # subway_entrance nodes (Gomis, Joaquim Folguera, etc.) are filtered out
    # so no lookup needed for those
    "peu del funicular": ["L7 (FGC)"], "les planes": ["L7 (FGC)"],
    "la floresta":     ["L7 (FGC)"], "valldoreix": ["L7 (FGC)"],
    "sant cugat":      ["S1 (FGC)", "S5 (FGC)"],
    "baixador de vallvidrera": ["L7 (FGC)"], "vallvidrera superior": ["L7 (FGC)"],
    # FGC Sarrià / Sant Cugat lines (L6, S1, S5, S2) — near upper Barcelona
    "el putxet":       ["L6 (FGC)"], "la bonanova":      ["S1 (FGC)", "S5 (FGC)"],
    "les tres torres": ["S1 (FGC)", "S5 (FGC)"], "sarrià": ["L6 (FGC)", "S1 (FGC)", "S5 (FGC)"],
    "muntaner":        ["L6 (FGC)"], "gràcia":           ["L6 (FGC)", "S1 (FGC)", "S5 (FGC)"],
    "provença":        ["L6 (FGC)"],
    # FGC Llobregat-Anoia line
    "pl. espanya":     ["L8 (FGC)", "L1", "L3"], "magòria - la campana": ["L8 (FGC)"],
    "ildefons cerdà":  ["L8 (FGC)"],
    # Tramvia
    "glòries":         ["T4 (Tram)"],
}

CATEGORY_MAP = {
    "supermarket":    {"amenity": ["supermarket"], "shop": ["supermarket", "convenience", "grocery"]},
    "restaurant":     {"amenity": ["restaurant", "cafe", "bar", "pub", "nightclub"]},
    "pharmacy":       {"amenity": ["pharmacy"]},
    "school":         {"amenity": ["school", "kindergarten"]},
    "park":           {"leisure": ["park", "garden"]},
    "bus_stop":       {"highway": ["bus_stop"]},
    "metro":          {"railway": ["station", "subway_entrance"], "station": ["subway"]},
    "hospital":       {"amenity": ["hospital", "clinic"]},
    "gym":            {"leisure": ["fitness_centre", "sports_centre"], "amenity": ["gym"]},
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
            import re
            route_ref = tags.get("route_ref", "")
            if route_ref:
                routes = [r.strip() for r in re.split(r'[;,\s]+', route_ref) if r.strip()]
            # Also check against fetched route relations
            stop_name_lower = name.lower()
            for route_name, stops_in_route in transit_routes.items():
                if any(stop_name_lower in s.lower() for s in stops_in_route):
                    if route_name not in routes:
                        routes.append(route_name)
            # Apply Barcelona metro/FGC lookup for stations missing route_ref
            if category == "metro" and not routes:
                known = _BCN_TRANSIT_LINES.get(stop_name_lower, [])
                routes = known

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

    # Deduplicate transit stops:
    # - Bus stops within 80m of each other → keep closest, merge route sets
    # - Metro entrances with same station name → keep closest, merge route sets
    result["bus_stop"] = _dedupe_transit(result["bus_stop"], radius_m=80)
    result["metro"]    = _dedupe_metro(result["metro"])

    return result


def _dedupe_transit(stops: list[dict], radius_m: int = 80) -> list[dict]:
    """Merge bus stops within radius_m of each other (opposite-direction stops of the same intersection)."""
    merged: list[dict] = []
    used = set()
    for i, stop in enumerate(stops):
        if i in used:
            continue
        cluster = [stop]
        for j, other in enumerate(stops[i + 1:], i + 1):
            if j in used:
                continue
            if haversine(stop["lat"], stop["lng"], other["lat"], other["lng"]) <= radius_m:
                cluster.append(other)
                used.add(j)
        # Merge: keep closest (first), union all route sets
        representative = dict(cluster[0])
        all_routes: list[str] = []
        seen_routes: set[str] = set()
        for s in cluster:
            for r in s.get("routes", []):
                if r not in seen_routes:
                    all_routes.append(r)
                    seen_routes.add(r)
        representative["routes"] = sorted(all_routes)
        merged.append(representative)
    return merged


def _dedupe_metro(stops: list[dict]) -> list[dict]:
    """Collapse multiple entrances of the same metro station into one (closest), merging routes."""
    seen_names: dict[str, dict] = {}
    for stop in stops:
        name = stop["name"].lower().strip()
        if name not in seen_names:
            seen_names[name] = dict(stop)
        else:
            # Already have this station; merge routes
            existing = seen_names[name]
            combined = set(existing.get("routes", [])) | set(stop.get("routes", []))
            existing["routes"] = sorted(combined)
    return list(seen_names.values())


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
    # Only classify as metro when it's an actual station node (station=subway),
    # NOT subway_entrance nodes — those are individual door-level entrance nodes
    # named after their street (e.g. "Gomis", "Joaquim Folguera") which are
    # confusingly different from the station itself.
    if station == "subway": return "metro"
    if railway == "station" and station in ("subway", "light_rail"): return "metro"
    if leisure in ["fitness_centre", "sports_centre"] or amenity == "gym": return "gym"
    if amenity == "library": return "library"
    if amenity in ["arts_centre", "cultural_centre", "community_centre"]: return "cultural_centre"
    if amenity in ["theatre", "cinema"]: return "theatre"
    if amenity == "marketplace": return "marketplace"
    return None
