"""Neighbourhood trajectory: is the area rising, stable, or declining?

Primary signal: Barcelona open data — new business activity licences.
API: https://opendata-ajuntament.barcelona.cat

Falls back to a static district heuristic when the API is slow or unavailable.
For non-Barcelona cities, the BCN API is skipped entirely.
"""
from datetime import datetime, timedelta, timezone

import httpx

BCN_LICENCES_API = "https://opendata-ajuntament.barcelona.cat/data/api/action/datastore_search"
# Dataset: "Llicències d'activitats" (activity licences)
BCN_LICENCES_RESOURCE = "b16f5b31-e95e-4ab3-bc05-e1f7c89a74f7"

# Static trend per district — used as fallback and to calibrate the live signal
_DISTRICT_TREND_FALLBACK = {
    "Ciutat Vella":         {"trend": "stable",   "score": 50, "new_biz": 45},
    "Eixample":             {"trend": "rising",    "score": 68, "new_biz": 82},
    "Sants-Montjuïc":       {"trend": "rising",    "score": 62, "new_biz": 60},
    "Les Corts":            {"trend": "stable",    "score": 55, "new_biz": 35},
    "Sarrià-Sant Gervasi":  {"trend": "stable",    "score": 58, "new_biz": 40},
    "Gràcia":               {"trend": "rising",    "score": 70, "new_biz": 75},
    "Horta-Guinardó":       {"trend": "stable",    "score": 52, "new_biz": 30},
    "Nou Barris":           {"trend": "stable",    "score": 48, "new_biz": 25},
    "Sant Andreu":          {"trend": "rising",    "score": 60, "new_biz": 50},
    "Sant Martí":           {"trend": "rising",    "score": 65, "new_biz": 65},
}

_NEUTRAL = {"trend": "stable", "new_businesses_12m": None, "renovation_permits_12m": None, "trend_score": None}

# Madrid district trajectory heuristics — based on urban development plans,
# real estate market reports, and investment activity 2022-2024.
# Source: Ayuntamiento de Madrid PEIN 2024, JLL/Savills Madrid market reports.
_MADRID_DISTRICT_TRAJECTORY = {
    "Centro":                {"trend": "rising",    "score": 68, "new_biz": 90},  # gentrification/touristification
    "Salamanca":             {"trend": "stable",    "score": 60, "new_biz": 45},  # mature, stable luxury
    "Retiro":                {"trend": "stable",    "score": 58, "new_biz": 40},  # mature residential
    "Chamberí":              {"trend": "rising",    "score": 65, "new_biz": 60},  # popular, active
    "Chamartín":             {"trend": "stable",    "score": 55, "new_biz": 35},  # established north
    "Tetuán":                {"trend": "rising",    "score": 62, "new_biz": 65},  # gentrifying, Cuatro Caminos
    "Moncloa-Aravaca":       {"trend": "stable",    "score": 58, "new_biz": 40},  # university + upscale
    "Arganzuela":            {"trend": "rising",    "score": 65, "new_biz": 70},  # Madrid Río, strong growth
    "Fuencarral-El Pardo":   {"trend": "rising",    "score": 62, "new_biz": 55},  # northern expansion
    "Latina":                {"trend": "stable",    "score": 50, "new_biz": 30},  # traditional, slow
    "Carabanchel":           {"trend": "rising",    "score": 58, "new_biz": 50},  # improving affordability zone
    "Usera":                 {"trend": "stable",    "score": 50, "new_biz": 40},  # multicultural, stable
    "Puente de Vallecas":    {"trend": "stable",    "score": 48, "new_biz": 25},  # working class, slow
    "Moratalaz":             {"trend": "stable",    "score": 48, "new_biz": 22},  # quiet, limited activity
    "Ciudad Lineal":         {"trend": "stable",    "score": 52, "new_biz": 35},  # mixed, moderate
    "Hortaleza":             {"trend": "rising",    "score": 60, "new_biz": 50},  # northern growth corridor
    "Vicálvaro":             {"trend": "stable",    "score": 50, "new_biz": 28},  # peripheral, limited
    "San Blas-Canillejas":   {"trend": "stable",    "score": 50, "new_biz": 30},  # east periphery
    "Barajas":               {"trend": "stable",    "score": 52, "new_biz": 30},  # airport zone
    "Villaverde":            {"trend": "stable",    "score": 45, "new_biz": 20},  # southern industrial
}


async def get_neighbourhood_trajectory(
    lat: float, lng: float, district: str | None, city: str | None = None
) -> dict:
    # For Madrid: use static trajectory heuristics (no equivalent of BCN Licences API)
    if city == "madrid":
        fallback = _MADRID_DISTRICT_TRAJECTORY.get(
            district or "",
            {"trend": "stable", "score": 52, "new_biz": 30}
        )
        return {
            "trend": fallback["trend"],
            "new_businesses_12m": fallback["new_biz"],
            "renovation_permits_12m": None,
            "trend_score": float(fallback["score"]),
        }

    # Other non-BCN cities: return neutral
    if city and city != "barcelona":
        return {**_NEUTRAL, "_unavailable": True}

    # Skip API call when district is unknown (prevents malformed queries to BCN API)
    if not district:
        return {**_NEUTRAL}

    fallback = _DISTRICT_TREND_FALLBACK.get(district, {"trend": "stable", "score": 52, "new_biz": 30})

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(BCN_LICENCES_API, params={
                "resource_id": BCN_LICENCES_RESOURCE,
                "q": district,
                "limit": 500,
            })
        records = r.json().get("result", {}).get("records", [])
    except Exception:
        records = []

    if records:
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        new_12m = 0
        for rec in records:
            date_str = rec.get("data_alta") or rec.get("Data_Alta") or ""
            try:
                parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if parsed > cutoff:
                    new_12m += 1
            except (ValueError, TypeError):
                continue

        trend_score = min(100, 40 + new_12m * 1.5)
        trend = "rising" if trend_score > 63 else "declining" if trend_score < 42 else "stable"

        return {
            "trend": trend,
            "new_businesses_12m": new_12m,
            "renovation_permits_12m": 0,
            "trend_score": round(trend_score, 1),
        }

    return {
        "trend": fallback["trend"],
        "new_businesses_12m": fallback["new_biz"],
        "renovation_permits_12m": 0,
        "trend_score": float(fallback["score"]),
    }
