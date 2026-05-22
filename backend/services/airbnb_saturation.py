"""Airbnb / tourist apartment saturation analysis.

Data source: Inside Airbnb (free, quarterly snapshots).
URLs:
  Barcelona: http://data.insideairbnb.com/spain/catalonia/barcelona/
  Valencia:  https://data.insideairbnb.com/spain/vc/valencia/2025-09-23/data/listings.csv.gz

CSVs are downloaded once and cached locally at ~/.cache/property_analyzer/.
Falls back to a district-level heuristic when data is unavailable.
"""
import csv
import gzip
import io
import math
import os
from pathlib import Path

import httpx

INSIDE_AIRBNB_URL = (
    "http://data.insideairbnb.com/spain/catalonia/barcelona/"
    "2024-09-15/data/listings.csv.gz"
)
INSIDE_AIRBNB_URL_VLC = (
    "https://data.insideairbnb.com/spain/vc/valencia/"
    "2025-09-23/data/listings.csv.gz"
)
_CACHE_PATH = Path.home() / ".cache" / "property_analyzer" / "airbnb_bcn.csv"
_CACHE_PATH_VLC = Path.home() / ".cache" / "property_analyzer" / "airbnb_vlc.csv"
_LISTINGS: list[dict] | None = None
_LISTINGS_VLC: list[dict] | None = None

# District-level fallback (rough % of housing stock that is tourist apartments)
_DISTRICT_FALLBACK = {
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


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def _ensure_listings() -> list[dict]:
    global _LISTINGS
    if _LISTINGS is not None:
        return _LISTINGS

    if _CACHE_PATH.exists():
        _LISTINGS = _load_csv(_CACHE_PATH.read_bytes())
        return _LISTINGS

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(INSIDE_AIRBNB_URL)
        r.raise_for_status()
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_bytes(r.content)
        _LISTINGS = _load_csv(r.content)
    except Exception:
        _LISTINGS = []

    return _LISTINGS


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


async def _ensure_listings_vlc() -> list[dict]:
    global _LISTINGS_VLC
    if _LISTINGS_VLC is not None:
        return _LISTINGS_VLC

    if _CACHE_PATH_VLC.exists():
        _LISTINGS_VLC = _load_csv(_CACHE_PATH_VLC.read_bytes())
        return _LISTINGS_VLC

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(INSIDE_AIRBNB_URL_VLC)
        r.raise_for_status()
        _CACHE_PATH_VLC.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH_VLC.write_bytes(r.content)
        _LISTINGS_VLC = _load_csv(r.content)
    except Exception:
        _LISTINGS_VLC = []

    return _LISTINGS_VLC


# Valencia district-level Airbnb fallback (2024, 9,009 listings total)
# Source: Inside Airbnb Valencia 2025-09-23 data distribution across districts
_VALENCIA_DISTRICT_FALLBACK = {
    "Ciutat Vella":      {"risk": "very_high", "count_500m": 250},  # historic core, highest density
    "L'Eixample":        {"risk": "high",      "count_500m": 120},
    "Extramurs":         {"risk": "medium",    "count_500m": 60},
    "Poblats Marítims":  {"risk": "high",      "count_500m": 130},  # Cabanyal beach area
    "El Pla del Real":   {"risk": "medium",    "count_500m": 55},
    "La Saïdia":         {"risk": "medium",    "count_500m": 45},
    "Campanar":          {"risk": "low",       "count_500m": 20},
    "L'Olivereta":       {"risk": "low",       "count_500m": 15},
    "Patraix":           {"risk": "low",       "count_500m": 12},
    "Jesús":             {"risk": "low",       "count_500m": 15},
    "Quatre Carreres":   {"risk": "low",       "count_500m": 18},
    "Camins al Grau":    {"risk": "medium",    "count_500m": 40},
    "Algirós":           {"risk": "low",       "count_500m": 20},
    "Benimaclet":        {"risk": "low",       "count_500m": 22},
    "Rascanya":          {"risk": "low",       "count_500m": 10},
    "Benicalap":         {"risk": "low",       "count_500m": 8},
    "Pobles del Nord":   {"risk": "low",       "count_500m": 5},
    "Pobles de l'Oest":  {"risk": "low",       "count_500m": 5},
    "Pobles del Sud":    {"risk": "low",       "count_500m": 5},
}

# Madrid district-level Airbnb risk heuristics (2024 estimates from Inside Airbnb Madrid)
_MADRID_DISTRICT_FALLBACK = {
    "Centro":             {"risk": "very_high", "count_500m": 200},
    "Salamanca":          {"risk": "high",      "count_500m": 120},
    "Retiro":             {"risk": "medium",    "count_500m": 60},
    "Chamberí":           {"risk": "medium",    "count_500m": 55},
    "Chamartín":          {"risk": "low",       "count_500m": 25},
    "Arganzuela":         {"risk": "medium",    "count_500m": 40},
    "Latina":             {"risk": "low",       "count_500m": 20},
    "Carabanchel":        {"risk": "low",       "count_500m": 15},
    "Tetuán":             {"risk": "medium",    "count_500m": 45},
    "Puente de Vallecas": {"risk": "low",       "count_500m": 10},
    "Hortaleza":          {"risk": "low",       "count_500m": 12},
    "Fuencarral-El Pardo":{"risk": "low",       "count_500m": 8},
}


async def get_airbnb_saturation(
    lat: float, lng: float, district: str | None = None, city: str | None = None
) -> dict:
    city_key = (city or "barcelona").lower()

    # For Madrid: BCN CSV has no useful data — use Madrid-specific district heuristics
    if city_key == "madrid":
        fallback = _MADRID_DISTRICT_FALLBACK.get(
            district or "", {"risk": "medium", "count_500m": 30}
        )
        return {
            "tourist_pct_building": None,
            "tourist_count_500m": None,
            "tourist_count_100m": None,
            "risk_label": fallback["risk"],
            "data_source": "district-heuristic",
        }

    # For Valencia: use Inside Airbnb Valencia CSV, fall back to district heuristics
    if city_key == "valencia":
        listings = await _ensure_listings_vlc()
        if not listings:
            fallback = _VALENCIA_DISTRICT_FALLBACK.get(district or "", {"risk": "medium", "count_500m": 30})
            return {
                "tourist_pct_building": None,
                "tourist_count_500m": None,
                "tourist_count_100m": None,
                "risk_label": fallback["risk"],
                "data_source": "district-heuristic",
            }
        nearby_500m = [l for l in listings if _haversine(lat, lng, l["lat"], l["lng"]) <= 500]
        nearby_100m = [l for l in listings if _haversine(lat, lng, l["lat"], l["lng"]) <= 100]
        nearby_40m  = [l for l in listings if _haversine(lat, lng, l["lat"], l["lng"]) <= 40]
        count_500m = len(nearby_500m)
        count_100m = len(nearby_100m)
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

    # Barcelona path: use Inside Airbnb BCN CSV
    listings = await _ensure_listings()

    if not listings:
        # InsideAirbnb CSV unavailable. Use district-level risk label only.
        # We intentionally do NOT show specific counts (100m / 500m) because the
        # district-level numbers are averages and would be misleading for a specific address.
        fallback = _DISTRICT_FALLBACK.get(district or "", {"risk": "medium"})
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
