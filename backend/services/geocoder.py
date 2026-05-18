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
    Returns {lat, lng, display_name, address, geocode_confidence, geocode_warning}.

    geocode_confidence: "high" = matched a specific building/street address
                        "low"  = best available match was a POI or ambiguous result
    geocode_warning:    human-readable explanation when confidence is "low", else None
    """
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{NOMINATIM_URL}/search",
            params={"q": address, "format": "json", "limit": 5, "addressdetails": 1},
            headers={"User-Agent": "PropertyAnalyzer/2.0 (contact@propertyanalyzer.app)"}
        )
        results = r.json()

    if not results:
        raise ValueError(f"Address not found: {address}")

    # Prefer residential results; fall back to first result if none qualify
    best = next((r for r in results if _is_residential(r)), None)
    confidence = "high"
    warning = None

    if best is None:
        best = results[0]
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

    return {
        "lat": float(best["lat"]),
        "lng": float(best["lon"]),
        "display_name": best["display_name"],
        "address": best.get("address", {}),
        "geocode_confidence": confidence,
        "geocode_warning": warning,
    }
