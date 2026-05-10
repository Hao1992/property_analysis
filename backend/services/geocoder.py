import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org"


async def geocode(address: str) -> dict:
    """Returns {lat, lng, display_name, address_components}"""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{NOMINATIM_URL}/search",
            params={"q": address, "format": "json", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": "PropertyAnalyzer/1.0 (contact@propertyanalyzer.app)"}
        )
        results = r.json()

    if not results:
        raise ValueError(f"Address not found: {address}")

    res = results[0]
    return {
        "lat": float(res["lat"]),
        "lng": float(res["lon"]),
        "display_name": res["display_name"],
        "address": res.get("address", {})
    }
