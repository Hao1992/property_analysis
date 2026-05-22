import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org"

# OSM classes/types that indicate a named POI rather than a street address.
# When Nominatim returns one of these, it matched a business/amenity, not a building.
_POI_CLASSES = {"amenity", "shop", "tourism", "leisure", "office", "healthcare"}
_POI_TYPES = {
    "clinic", "dentist", "doctors", "hospital", "pharmacy",
    "restaurant", "cafe", "bar", "pub", "fast_food",
    "hotel", "hostel", "guest_house",
    "supermarket", "convenience", "clothes",
    "bank", "post_office", "police",
}

# Supported cities with their bounding boxes [south, west, north, east]
# Used to reject geocode results that land outside the intended city.
_CITY_VIEWBOXES = {
    "barcelona": [41.310, 2.052, 41.470, 2.228],
    "madrid":    [40.312, -3.834, 40.644, -3.520],
}

# Nominatim state/county names → our city keys
_STATE_TO_CITY = {
    "cataluña": "barcelona",
    "catalonia": "barcelona",
    "catalunya": "barcelona",
    "comunidad de madrid": "madrid",
    "community of madrid": "madrid",
    "madrid": "madrid",
}
_CITY_TO_CITY = {
    "barcelona": "barcelona",
    "madrid": "madrid",
}


def _detect_city(addr: dict) -> str | None:
    """Infer supported city from Nominatim address components. Returns None if unsupported."""
    # Check explicit city field first (most reliable)
    city_raw = (addr.get("city") or addr.get("town") or addr.get("municipality") or "").lower()
    if city_raw in _CITY_TO_CITY:
        return _CITY_TO_CITY[city_raw]

    # Fall back to state/community
    state_raw = (addr.get("state") or addr.get("region") or "").lower()
    for key, city in _STATE_TO_CITY.items():
        if key in state_raw:
            return city

    return None


def _in_city_bounds(lat: float, lng: float, city: str) -> bool:
    """Return True if coordinates fall within the city's bounding box."""
    if city not in _CITY_VIEWBOXES:
        return False
    s, w, n, e = _CITY_VIEWBOXES[city]
    return s <= lat <= n and w <= lng <= e


def _is_residential(result: dict) -> bool:
    """Return True if the Nominatim result looks like a specific street address."""
    addr = result.get("address", {})
    osm_class = result.get("class", "")
    osm_type = result.get("type", "")

    # Reject named POIs
    if osm_class in _POI_CLASSES:
        return False
    if osm_type in _POI_TYPES:
        return False
    # Reject results where the address block contains a named amenity
    if "amenity" in addr or "shop" in addr or "tourism" in addr:
        return False
    # Require at minimum a road name (bare neighbourhood returns don't qualify)
    if not addr.get("road"):
        return False

    return True


async def geocode(address: str) -> dict:
    """
    Returns {lat, lng, display_name, address, geocode_confidence, geocode_warning,
             city, region, country_code}.

    city:             "barcelona" | "madrid" | None (unsupported/unknown)
    region:           "catalunya" | "madrid" | None
    country_code:     ISO 3166-1 alpha-2 (e.g. "es")
    geocode_confidence: "high" | "low"
    geocode_warning:  human-readable explanation when confidence is "low", else None
    """
    # Detect if user mentioned a supported city in the query for targeted search
    addr_lower = address.lower()
    _hint_city = None
    if "madrid" in addr_lower:
        _hint_city = "madrid"
    elif "barcelona" in addr_lower or "bcn" in addr_lower:
        _hint_city = "barcelona"

    params: dict = {"q": address, "format": "json", "limit": 5, "addressdetails": 1, "countrycodes": "es"}
    # Add viewbox constraint when city hint is detected to reduce false positives
    if _hint_city and _hint_city in _CITY_VIEWBOXES:
        s, w, n, e = _CITY_VIEWBOXES[_hint_city]
        params["viewbox"] = f"{w},{n},{e},{s}"   # left,top,right,bottom
        params["bounded"] = "0"   # soft constraint: prefer within viewbox, but fall back outside

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{NOMINATIM_URL}/search",
            params=params,
            headers={"User-Agent": "PropertyAnalyzer/2.0 (contact@propertyanalyzer.app)"}
        )
        results = r.json()

    if not results:
        raise ValueError(f"Address not found: {address}")

    # Prefer residential results within the hinted city; fall back to first residential
    def _score(result: dict) -> int:
        """Higher = better candidate."""
        score = 0
        if _is_residential(result):
            score += 10
        if _hint_city:
            detected = _detect_city(result.get("address", {}))
            if detected == _hint_city:
                score += 5
            lat_, lng_ = float(result.get("lat", 0)), float(result.get("lon", 0))
            if _in_city_bounds(lat_, lng_, _hint_city):
                score += 3
        return score

    results_sorted = sorted(results, key=_score, reverse=True)
    best = results_sorted[0] if results_sorted else results[0]
    confidence = "high"
    warning = None

    if not _is_residential(best):
        confidence = "low"
        matched_name = (
            best.get("address", {}).get("amenity")
            or best.get("address", {}).get("shop")
            or best.get("display_name", "unknown location").split(",")[0]
        )
        warning = (
            f"Address matched '{matched_name}' instead of a street address. "
            "Verify the address shown below is correct — analysis data may be for "
            "the wrong location."
        )

    addr_components = best.get("address", {})
    lat = float(best["lat"])
    lng = float(best["lon"])
    country_code = addr_components.get("country_code", "").lower()
    city = _detect_city(addr_components)

    # Sanity check: if we detected a supported city, verify coordinates are inside it.
    # This catches cases like "Calle Gran Vía 50, Madrid" geocoding to rural Arganda del Rey.
    if city and not _in_city_bounds(lat, lng, city):
        city = None
        if confidence == "high":
            confidence = "low"
            warning = (
                "Geocode result appears to be outside the expected city boundaries. "
                "Verify the address below is correct."
            )

    # Derive region from city
    _city_to_region = {"barcelona": "catalunya", "madrid": "madrid"}
    region = _city_to_region.get(city) if city else None

    return {
        "lat": lat,
        "lng": lng,
        "display_name": best["display_name"],
        "address": addr_components,
        "geocode_confidence": confidence,
        "geocode_warning": warning,
        "city": city,
        "region": region,
        "country_code": country_code,
    }
