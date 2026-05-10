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

INSIDE_AIRBNB_URL = (
    "http://data.insideairbnb.com/spain/catalonia/barcelona/"
    "2024-09-15/data/listings.csv.gz"
)
_CACHE_PATH = Path.home() / ".cache" / "property_analyzer" / "airbnb_bcn.csv"
_LISTINGS: list[dict] | None = None

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


async def get_airbnb_saturation(lat: float, lng: float, district: str = "Eixample") -> dict:
    listings = await _ensure_listings()

    if not listings:
        fallback = _DISTRICT_FALLBACK.get(district, {"risk": "medium", "count_500m": 40})
        return {
            "tourist_pct_building": None,
            "tourist_count_500m": fallback["count_500m"],
            "tourist_count_100m": max(1, fallback["count_500m"] // 8),
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
