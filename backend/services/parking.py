"""Parking analysis: zone type by district + nearby OSM garages."""
import httpx
import math
from typing import Optional

_HEADERS = {"User-Agent": "BeyondPrice/2.0 parking-analysis"}
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

_DISTRICT_ZONE: dict[str, str] = {
    "Eixample":            "zona_verde",
    "Gràcia":              "zona_verde",
    "Les Corts":           "zona_verde",
    "Ciutat Vella":        "zona_verde",
    "Sants-Montjuïc":      "zona_azul",
    "Sant Martí":          "zona_azul",
    "Horta-Guinardó":      "zona_azul",
    "Sant Andreu":         "zona_azul",
    "Nou Barris":          "mixed",
    "Sarrià-Sant Gervasi": "free",
}

_DISTRICT_GARAGE_MONTHLY: dict[str, int] = {
    "Eixample":            180,
    "Gràcia":              160,
    "Les Corts":           155,
    "Ciutat Vella":        190,
    "Sants-Montjuïc":      140,
    "Sant Martí":          145,
    "Horta-Guinardó":      120,
    "Sant Andreu":         125,
    "Nou Barris":          110,
    "Sarrià-Sant Gervasi": 170,
}

# Non-resident rates; ~120 paid hours/month (realistic commuter estimate)
_ZONE_HOURLY: dict[str, float] = {
    "zona_verde": 3.50,
    "zona_azul":  2.50,
    "mixed":      2.50,
    "free":       0.0,
}
_MONTHLY_HOURS = 120


def _distance_m(lat1, lng1, lat2, lng2) -> float:
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


async def _fetch_garages(lat: float, lng: float, radius: int = 400) -> list[dict]:
    query = f"""
[out:json][timeout:20];
(
  node["amenity"="parking"]["parking"~"multi-storey|underground"](around:{radius},{lat},{lng});
  way["amenity"="parking"]["parking"~"multi-storey|underground"](around:{radius},{lat},{lng});
  node["amenity"="parking_entrance"](around:{radius},{lat},{lng});
);
out center tags;
"""
    try:
        async with httpx.AsyncClient(timeout=25, headers=_HEADERS) as client:
            r = await client.post(OVERPASS_URL, data={"data": query})
            r.raise_for_status()
            elements = r.json().get("elements", [])
    except Exception:
        return []

    garages = []
    seen: set[str] = set()
    for el in elements:
        tags = el.get("tags", {})
        # skip private
        if tags.get("access") in ("private", "no"):
            continue
        # coordinates
        if "center" in el:
            clat, clng = el["center"]["lat"], el["center"]["lon"]
        else:
            clat, clng = el.get("lat", lat), el.get("lon", lng)
        name = tags.get("name") or tags.get("operator") or tags.get("brand") or "Parking"
        dedup_key = f"{round(clat,4)},{round(clng,4)}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        dist = round(_distance_m(lat, lng, clat, clng))
        garages.append({"name": name, "distance_m": dist, "lat": clat, "lng": clng})

    return sorted(garages, key=lambda g: g["distance_m"])


async def get_parking_analysis(
    lat: float,
    lng: float,
    district: str,
    has_private_parking: bool,
    has_car: bool,
) -> dict:
    garages_raw = await _fetch_garages(lat, lng)
    garage_monthly = _DISTRICT_GARAGE_MONTHLY.get(district, 150)
    zone_type = _DISTRICT_ZONE.get(district, "zona_azul")
    hourly = _ZONE_HOURLY.get(zone_type, 2.50)
    zone_monthly = round(hourly * _MONTHLY_HOURS) if hourly > 0 else None

    nearby: list[dict] = []
    for g in garages_raw[:3]:
        nearby.append({
            "name": g["name"],
            "distance_m": float(g["distance_m"]),
            "monthly_est_eur": garage_monthly,
        })

    parking_needed = has_car and not has_private_parking

    # Recommended option
    if has_private_parking:
        option = "private"
        rec_monthly = None
    elif zone_monthly is None:
        option = "free"
        rec_monthly = 0
    elif garages_raw and garage_monthly <= (zone_monthly or 9999):
        option = "garage"
        rec_monthly = garage_monthly
    elif zone_monthly:
        option = "street"
        rec_monthly = zone_monthly
    else:
        option = "free"
        rec_monthly = 0

    return {
        "has_private_parking":     has_private_parking,
        "nearby_garages_count":    len(garages_raw),
        "nearby_garages":          nearby,
        "zone_type":               zone_type,
        "zone_monthly_eur":        zone_monthly,
        "recommended_option":      option,
        "recommended_monthly_eur": rec_monthly if not has_private_parking else None,
        "parking_needed":          parking_needed,
    }
