"""Airbnb / tourist apartment saturation analysis.

Data source: Inside Airbnb Barcelona (free, quarterly snapshots).
URL: http://insideairbnb.com/get-the-data/

The CSV is downloaded once and cached locally at ~/.cache/property_analyzer/airbnb_bcn.csv.
Falls back to a district-level heuristic when data is unavailable.
"""
import csv
import gzip
import io
import math
import os
from pathlib import Path

import httpx

INSIDE_AIRBNB_URL_BCN = (
    "http://data.insideairbnb.com/spain/catalonia/barcelona/"
    "2024-09-15/data/listings.csv.gz"
)
INSIDE_AIRBNB_URL_MAD = (
    "http://data.insideairbnb.com/spain/comunidad-de-madrid/madrid/"
    "2025-09-14/visualisations/listings.csv"
)

# Legacy alias for backward compatibility
INSIDE_AIRBNB_URL = INSIDE_AIRBNB_URL_BCN

_CACHE_PATH_BCN = Path.home() / ".cache" / "property_analyzer" / "airbnb_bcn.csv"
_CACHE_PATH_MAD = Path.home() / ".cache" / "property_analyzer" / "airbnb_mad.csv"
# Legacy alias
_CACHE_PATH = _CACHE_PATH_BCN

_LISTINGS_BCN: list[dict] | None = None
_LISTINGS_MAD: list[dict] | None = None

# District-level fallback — Barcelona
_DISTRICT_FALLBACK_BCN = {
    "Ciutat Vella":         {"risk": "very_high", "count_500m": 180},
    "Eixample":             {"risk": "high",      "count_500m": 95},
    "Sants-Montjuïc":       {"risk": "medium",    "count_500m": 45},
    "Les Corts":            {"risk": "low",        "count_500m": 20},
    "Sarrià-Sant Gervasi":  {"risk": "low",        "count_500m": 25},
    "Gràcia":               {"risk": "medium",     "count_500m": 55},
    "Horta-Guinardó":       {"risk": "low",        "count_500m": 18},
    "Nou Barris":           {"risk": "low",        "count_500m": 12},
    "Sant Andreu":          {"risk": "low",        "count_500m": 15},
    "Sant Martí":           {"risk": "medium",     "count_500m": 40},
}
# Legacy alias
_DISTRICT_FALLBACK = _DISTRICT_FALLBACK_BCN

# District-level fallback — Madrid (based on Sep 2025 Inside Airbnb + Plan RESIDE impact)
_DISTRICT_FALLBACK_MAD = {
    "Centro":              {"risk": "very_high", "count_500m": 210},
    "Arganzuela":          {"risk": "medium",    "count_500m": 55},
    "Retiro":              {"risk": "medium",    "count_500m": 40},
    "Salamanca":           {"risk": "high",      "count_500m": 90},
    "Chamartín":           {"risk": "medium",    "count_500m": 35},
    "Tetuán":              {"risk": "medium",    "count_500m": 45},
    "Chamberí":            {"risk": "high",      "count_500m": 70},
    "Fuencarral-El Pardo": {"risk": "low",       "count_500m": 15},
    "Moncloa-Aravaca":     {"risk": "low",       "count_500m": 20},
    "Latina":              {"risk": "low",        "count_500m": 18},
    "Carabanchel":         {"risk": "low",        "count_500m": 12},
    "Usera":               {"risk": "low",        "count_500m": 15},
    "Puente de Vallecas":  {"risk": "low",        "count_500m": 10},
    "Moratalaz":           {"risk": "low",        "count_500m": 8},
    "Ciudad Lineal":       {"risk": "low",        "count_500m": 12},
    "Hortaleza":           {"risk": "low",        "count_500m": 10},
    "Villaverde":          {"risk": "low",        "count_500m": 5},
    "Villa de Vallecas":   {"risk": "low",        "count_500m": 8},
    "Vicálvaro":           {"risk": "low",        "count_500m": 6},
    "San Blas-Canillejas": {"risk": "low",        "count_500m": 8},
    "Barajas":             {"risk": "low",        "count_500m": 5},
}


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def _ensure_listings(city: str = "barcelona") -> list[dict]:
    global _LISTINGS_BCN, _LISTINGS_MAD
    is_madrid = city == "madrid"
    listings_ref = _LISTINGS_MAD if is_madrid else _LISTINGS_BCN
    cache_path = _CACHE_PATH_MAD if is_madrid else _CACHE_PATH_BCN
    url = INSIDE_AIRBNB_URL_MAD if is_madrid else INSIDE_AIRBNB_URL_BCN

    if listings_ref is not None:
        return listings_ref

    if cache_path.exists():
        data = _load_csv(cache_path.read_bytes())
        if is_madrid:
            _LISTINGS_MAD = data
        else:
            _LISTINGS_BCN = data
        return data

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(url)
        r.raise_for_status()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(r.content)
        data = _load_csv(r.content)
    except Exception:
        data = []

    if is_madrid:
        _LISTINGS_MAD = data
    else:
        _LISTINGS_BCN = data
    return data


def _load_csv(data: bytes) -> list[dict]:
    try:
        raw = gzip.decompress(data)
    except Exception:
        raw = data
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))
    rows = []
    for row in reader:
        try:
            lat = float(row.get("latitude") or 0)
            lng = float(row.get("longitude") or 0)
            if lat and lng:
                rows.append({"lat": lat, "lng": lng})
        except (ValueError, TypeError):
            continue
    return rows


async def get_airbnb_saturation(lat: float, lng: float, district: str = "Eixample", city: str = "barcelona") -> dict:
    listings = await _ensure_listings(city=city)
    fallback_map = _DISTRICT_FALLBACK_MAD if city == "madrid" else _DISTRICT_FALLBACK_BCN

    if not listings:
        # InsideAirbnb CSV unavailable. Use district-level risk label only.
        # We intentionally do NOT show specific counts (100m / 500m) because the
        # district-level numbers are averages and would be misleading for a specific address.
        fallback = fallback_map.get(district, {"risk": "medium"})
        return {
            "tourist_pct_building": None,
            "tourist_count_500m": None,   # not available — district fallback only
            "tourist_count_100m": None,   # not available — district fallback only
            "risk_label": fallback["risk"],
            "data_source": "district-heuristic",
        }

    nearby_500m = [l for l in listings if _haversine(lat, lng, l["lat"], l["lng"]) <= 500]
    nearby_100m = [l for l in listings if _haversine(lat, lng, l["lat"], l["lng"]) <= 100]
    nearby_40m  = [l for l in listings if _haversine(lat, lng, l["lat"], l["lng"]) <= 40]

    count_500m = len(nearby_500m)
    count_100m = len(nearby_100m)
    # Proxy for same-building saturation: listings within 40m, assuming ~8 units/building
    tourist_pct_building = round(min(100.0, len(nearby_40m) / 8 * 100), 1)

    risk = (
        "very_high" if tourist_pct_building >= 40 or count_500m > 150 else
        "high"      if tourist_pct_building >= 20 or count_500m > 80  else
        "medium"    if tourist_pct_building >= 10 or count_500m > 30  else
        "low"
    )

    return {
        "tourist_pct_building": tourist_pct_building,
        "tourist_count_500m": count_500m,
        "tourist_count_100m": count_100m,
        "risk_label": risk,
        "data_source": "Inside Airbnb",
    }
