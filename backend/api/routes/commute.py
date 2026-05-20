"""
Commute time analysis using OSRM (OpenStreetMap Routing Machine).

Free, open-source routing engine. No API key required.
Public instance: router.project-osrm.org

Modes: foot, bike, driving (car), transit (bus approximation via walking + bus factor)
"""
import asyncio
import httpx
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Public OSRM instances — try in order
_OSRM_ENDPOINTS = {
    "foot":    "https://router.project-osrm.org/route/v1/foot",
    "bike":    "https://router.project-osrm.org/route/v1/bike",
    "driving": "https://router.project-osrm.org/route/v1/driving",
}

# BCN metro speed proxy: OSRM can't route metro, so we estimate:
# average metro speed including wait time is ~25 km/h in BCN.
_METRO_AVG_SPEED_KMH = 25.0


class CommuteRequest(BaseModel):
    home_lat: float
    home_lng: float
    work_lat: float
    work_lng: float
    work_address: str = ""


class CommuteMode(BaseModel):
    mode: str
    mode_zh: str
    duration_minutes: int | None
    distance_km: float | None
    note: str
    note_zh: str
    quality: str   # "great" | "ok" | "long"


class CommuteResponse(BaseModel):
    work_address: str
    modes: list[CommuteMode]
    recommendation: str
    recommendation_zh: str


def _quality(minutes: int | None) -> str:
    if minutes is None:
        return "unknown"
    if minutes <= 15:
        return "great"
    if minutes <= 35:
        return "ok"
    return "long"


async def _osrm_route(mode: str, origin_lng: float, origin_lat: float,
                       dest_lng: float, dest_lat: float) -> tuple[int | None, float | None]:
    """Returns (duration_seconds, distance_meters) or (None, None) on failure."""
    endpoint = _OSRM_ENDPOINTS.get(mode)
    if not endpoint:
        return None, None
    url = f"{endpoint}/{origin_lng},{origin_lat};{dest_lng},{dest_lat}?overview=false"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            routes = data.get("routes", [])
            if not routes:
                return None, None
            route = routes[0]
            return int(route["duration"]), route["distance"]
    except Exception as exc:
        logger.warning("OSRM %s routing failed: %s", mode, exc)
        return None, None


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    import math
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/commute", response_model=CommuteResponse)
async def calculate_commute(req: CommuteRequest) -> CommuteResponse:
    for coord, name in [(req.home_lat, 'home_lat'), (req.home_lng, 'home_lng'),
                        (req.work_lat, 'work_lat'), (req.work_lng, 'work_lng')]:
        if not (-90 <= coord <= 90 if 'lat' in name else -180 <= coord <= 180):
            raise HTTPException(status_code=422, detail=f"Invalid coordinate: {name}")

    # Fetch foot + bike + driving in parallel
    foot_task   = _osrm_route("foot",    req.home_lng, req.home_lat, req.work_lng, req.work_lat)
    bike_task   = _osrm_route("bike",    req.home_lng, req.home_lat, req.work_lng, req.work_lat)
    driving_task = _osrm_route("driving", req.home_lng, req.home_lat, req.work_lng, req.work_lat)

    (foot_dur, foot_dist), (bike_dur, bike_dist), (drive_dur, drive_dist) = await asyncio.gather(
        foot_task, bike_task, driving_task
    )

    # OSRM public demo server sometimes returns driving-speed data for foot profile.
    # Walking speed cannot exceed 8 km/h; if implied speed > 8 km/h, recalculate at 5 km/h.
    if foot_dur is not None and foot_dist is not None and foot_dur > 0:
        implied_speed_kmh = (foot_dist / 1000) / (foot_dur / 3600)
        if implied_speed_kmh > 8:
            foot_dur = int(foot_dist / (5000 / 3600))  # seconds at 5 km/h

    # Bike speed cannot reasonably exceed 25 km/h average; if so, recalculate at 20 km/h.
    if bike_dur is not None and bike_dist is not None and bike_dur > 0:
        implied_speed_kmh = (bike_dist / 1000) / (bike_dur / 3600)
        if implied_speed_kmh > 25:
            bike_dur = int(bike_dist / (20000 / 3600))  # seconds at 20 km/h

    # Metro estimate: straight-line distance / 25 km/h + 5 min avg wait
    straight_km = _haversine_km(req.home_lat, req.home_lng, req.work_lat, req.work_lng)
    metro_minutes = round(straight_km / _METRO_AVG_SPEED_KMH * 60 + 5)

    modes: list[CommuteMode] = []

    if foot_dur is not None:
        mins = round(foot_dur / 60)
        modes.append(CommuteMode(
            mode="Walking", mode_zh="步行",
            duration_minutes=mins,
            distance_km=round(foot_dist / 1000, 1) if foot_dist else None,
            note=f"{mins} min walk",
            note_zh=f"步行 {mins} 分钟",
            quality=_quality(mins),
        ))

    if bike_dur is not None:
        mins = round(bike_dur / 60)
        modes.append(CommuteMode(
            mode="Bike / Bicing", mode_zh="自行车 / Bicing",
            duration_minutes=mins,
            distance_km=round(bike_dist / 1000, 1) if bike_dist else None,
            note=f"{mins} min by bike. BCN Bicing subscription ~€50/yr.",
            note_zh=f"骑行 {mins} 分钟。Barcelona Bicing年卡约 €50。",
            quality=_quality(mins),
        ))

    # Metro estimate always shown (straight-line proxy)
    modes.append(CommuteMode(
        mode="Metro (estimated)", mode_zh="地铁（估算）",
        duration_minutes=metro_minutes,
        distance_km=round(straight_km, 1),
        note=f"~{metro_minutes} min estimated (straight-line ÷ 25 km/h + 5 min wait). Verify on TMB planner.",
        note_zh=f"估算约 {metro_minutes} 分钟（直线距离÷25km/h + 5分钟等车）。请在TMB官网确认实际路线。",
        quality=_quality(metro_minutes),
    ))

    if drive_dur is not None:
        mins = round(drive_dur / 60)
        modes.append(CommuteMode(
            mode="Car (off-peak)", mode_zh="开车（非高峰）",
            duration_minutes=mins,
            distance_km=round(drive_dist / 1000, 1) if drive_dist else None,
            note=f"{mins} min driving (off-peak). Peak hours add 50–100%. Parking in BCN: €80–200/mo.",
            note_zh=f"非高峰驾车 {mins} 分钟。高峰期可增加50–100%。巴塞罗那停车费 €80–200/月。",
            quality=_quality(mins),
        ))

    # Recommendation based on best mode
    best = min(
        (m for m in modes if m.duration_minutes is not None and m.mode != "Car (off-peak)"),
        key=lambda m: m.duration_minutes or 999,
        default=None,
    )
    if best and best.duration_minutes is not None and best.duration_minutes <= 15:
        rec = f"Excellent location for commuting — {best.duration_minutes} min by {best.mode}."
        rec_zh = f"通勤极为便利 — {best.mode_zh} {best.duration_minutes} 分钟可达。"
    elif best and best.duration_minutes is not None and best.duration_minutes <= 30:
        rec = f"Reasonable commute — {best.duration_minutes} min by {best.mode}."
        rec_zh = f"通勤尚可 — {best.mode_zh} {best.duration_minutes} 分钟可达。"
    else:
        rec = "Commute may be significant. Consider metro routes and peak-hour timing."
        rec_zh = "通勤距离较长，建议查看地铁路线及高峰期时间安排。"

    return CommuteResponse(
        work_address=req.work_address,
        modes=modes,
        recommendation=rec,
        recommendation_zh=rec_zh,
    )
