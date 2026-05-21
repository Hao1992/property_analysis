"""Parking analysis backed by official Area Verda street-segment data."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "BeyondPrice/2.0 parking-analysis"}
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

AREA_VERDA_MAP_URL = "https://areaverda.cat/en/map"
AREA_VERDA_JSON_URL = os.getenv(
    "AREA_VERDA_JSON_URL",
    "https://areaverda.cat/sites/default/files/GetMappingObjects.json",
)
AREA_VERDA_CACHE_PATH = Path(
    os.getenv("AREA_VERDA_CACHE_PATH", "/tmp/area_verda_mapping_objects.json")
)
AREA_VERDA_META_PATH = AREA_VERDA_CACHE_PATH.with_suffix(".meta.json")
AREA_VERDA_CACHE_TTL_SECONDS = int(os.getenv("AREA_VERDA_CACHE_TTL_SECONDS", "86400"))
AREA_VERDA_SEGMENT_RADIUS_M = int(os.getenv("AREA_VERDA_SEGMENT_RADIUS_M", "250"))
AREA_VERDA_SEGMENT_LIMIT = int(os.getenv("AREA_VERDA_SEGMENT_LIMIT", "8"))
UNVERIFIED_MONTHLY_PRICE_SENTINEL = -1

_OFFICIAL_SEGMENT_TYPES = {
    2: "zona_azul",
    3: "zona_verde",
    4: "resident",
    5: "dum",
}


@dataclass(frozen=True)
class AreaVerdaSegment:
    map_object_id: str
    type_id: int
    zone_type: str
    location: str | None
    tariff: str | None
    timetable: str | None
    places: str | None
    resident_zone: str | None
    dum_zone: str | None
    coordinates: list[tuple[float, float]]
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class AreaVerdaResidentZone:
    code: str
    coordinates: list[tuple[float, float]]
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class AreaVerdaData:
    segments: list[AreaVerdaSegment]
    resident_zones: list[AreaVerdaResidentZone]
    last_modified: str | None
    fetched_at: float


_area_verda_data: AreaVerdaData | None = None
_area_verda_lock = asyncio.Lock()


def _distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _project(lat: float, lng: float, origin_lat: float) -> tuple[float, float]:
    R = 6371000
    x = math.radians(lng) * R * math.cos(math.radians(origin_lat))
    y = math.radians(lat) * R
    return x, y


def _point_segment_distance_m(
    point: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _polyline_distance_m(
    lat: float,
    lng: float,
    coordinates: list[tuple[float, float]],
) -> float:
    if not coordinates:
        return float("inf")

    projected = [_project(c_lat, c_lng, lat) for c_lat, c_lng in coordinates]
    point = _project(lat, lng, lat)
    if len(projected) == 1:
        return math.hypot(point[0] - projected[0][0], point[1] - projected[0][1])

    return min(
        _point_segment_distance_m(point, projected[i], projected[i + 1])
        for i in range(len(projected) - 1)
    )


def _bbox_for(coordinates: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lats = [lat for lat, _ in coordinates]
    lngs = [lng for _, lng in coordinates]
    return min(lats), min(lngs), max(lats), max(lngs)


def _bbox_near(
    lat: float,
    lng: float,
    bbox: tuple[float, float, float, float],
    radius_m: int,
) -> bool:
    lat_pad = radius_m / 111_320
    lng_pad = radius_m / max(1, 111_320 * math.cos(math.radians(lat)))
    min_lat, min_lng, max_lat, max_lng = bbox
    return (
        min_lat - lat_pad <= lat <= max_lat + lat_pad
        and min_lng - lng_pad <= lng <= max_lng + lng_pad
    )


def _point_in_polygon(lat: float, lng: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, (poly_lat, poly_lng) in enumerate(polygon):
        prev_lat, prev_lng = polygon[j]
        intersects = (poly_lat > lat) != (prev_lat > lat)
        if intersects:
            cross_lng = (prev_lng - poly_lng) * (lat - poly_lat) / (prev_lat - poly_lat + 1e-20) + poly_lng
            if lng < cross_lng:
                inside = not inside
        j = i
    return inside


def _visible_props(feature: dict[str, Any]) -> dict[str, str]:
    props: dict[str, str] = {}
    for item in feature.get("extendedProperties") or []:
        key = item.get("Key")
        value = item.get("Value")
        if item.get("Visible") and key and value is not None:
            props[str(key)] = str(value)
    return props


def _parse_coordinates(raw: Any) -> list[tuple[float, float]]:
    if not isinstance(raw, list):
        return []

    coordinates: list[tuple[float, float]] = []
    for item in raw:
        if (
            isinstance(item, list)
            and len(item) >= 2
            and isinstance(item[0], (int, float))
            and isinstance(item[1], (int, float))
        ):
            coordinates.append((float(item[0]), float(item[1])))
    return coordinates


def _build_area_verda_data(
    payload: dict[str, Any],
    last_modified: str | None,
) -> AreaVerdaData:
    segments: list[AreaVerdaSegment] = []
    resident_zones: list[AreaVerdaResidentZone] = []

    for feature in payload.get("features", []):
        type_id = feature.get("mapObjectTypeId")
        representation = feature.get("mapRepresentation") or {}
        props = _visible_props(feature)

        if type_id in _OFFICIAL_SEGMENT_TYPES:
            coordinates = _parse_coordinates(representation.get("coordinates"))
            if len(coordinates) < 2:
                continue

            segments.append(
                AreaVerdaSegment(
                    map_object_id=str(feature.get("mapObjectId") or ""),
                    type_id=int(type_id),
                    zone_type=_OFFICIAL_SEGMENT_TYPES[int(type_id)],
                    location=props.get("Ubicacion"),
                    tariff=props.get("Tarifa"),
                    timetable=props.get("Horario"),
                    places=props.get("Plazas"),
                    resident_zone=props.get("Zona de Resident"),
                    dum_zone=props.get("ZonaDUM"),
                    coordinates=coordinates,
                    bbox=_bbox_for(coordinates),
                )
            )
        elif type_id == 8:
            raw_coordinates = representation.get("coordinates") or []
            ring = raw_coordinates[0] if raw_coordinates and isinstance(raw_coordinates[0], list) else []
            coordinates = _parse_coordinates(ring)
            code = props.get("Codi Zona")
            if code and len(coordinates) >= 3:
                resident_zones.append(
                    AreaVerdaResidentZone(
                        code=code,
                        coordinates=coordinates,
                        bbox=_bbox_for(coordinates),
                    )
                )

    return AreaVerdaData(
        segments=segments,
        resident_zones=resident_zones,
        last_modified=last_modified,
        fetched_at=time.time(),
    )


def _read_cached_area_verda_payload() -> tuple[dict[str, Any], str | None] | None:
    if not AREA_VERDA_CACHE_PATH.exists():
        return None

    try:
        payload = json.loads(AREA_VERDA_CACHE_PATH.read_text())
        last_modified = None
        if AREA_VERDA_META_PATH.exists():
            meta = json.loads(AREA_VERDA_META_PATH.read_text())
            last_modified = meta.get("last_modified")
        return payload, last_modified
    except Exception as exc:
        logger.warning("Could not read Area Verda cache: %s", exc)
        return None


def _write_cached_area_verda_payload(payload: dict[str, Any], last_modified: str | None) -> None:
    try:
        AREA_VERDA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = AREA_VERDA_CACHE_PATH.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False))
        tmp_path.replace(AREA_VERDA_CACHE_PATH)
        AREA_VERDA_META_PATH.write_text(
            json.dumps({"last_modified": last_modified, "cached_at": time.time()})
        )
    except Exception as exc:
        logger.warning("Could not write Area Verda cache: %s", exc)


async def _download_area_verda_payload() -> tuple[dict[str, Any], str | None]:
    async with httpx.AsyncClient(timeout=45, headers=_HEADERS) as client:
        response = await client.get(AREA_VERDA_JSON_URL)
        response.raise_for_status()
        return response.json(), response.headers.get("Last-Modified")


async def _get_area_verda_data() -> AreaVerdaData | None:
    global _area_verda_data

    now = time.time()
    if _area_verda_data and now - _area_verda_data.fetched_at < AREA_VERDA_CACHE_TTL_SECONDS:
        return _area_verda_data

    async with _area_verda_lock:
        now = time.time()
        if _area_verda_data and now - _area_verda_data.fetched_at < AREA_VERDA_CACHE_TTL_SECONDS:
            return _area_verda_data

        cached_payload = _read_cached_area_verda_payload()
        cache_is_fresh = (
            cached_payload is not None
            and AREA_VERDA_CACHE_PATH.exists()
            and now - AREA_VERDA_CACHE_PATH.stat().st_mtime < AREA_VERDA_CACHE_TTL_SECONDS
        )
        if cache_is_fresh and cached_payload:
            payload, last_modified = cached_payload
            _area_verda_data = _build_area_verda_data(payload, last_modified)
            return _area_verda_data

        try:
            payload, last_modified = await _download_area_verda_payload()
            _write_cached_area_verda_payload(payload, last_modified)
            _area_verda_data = _build_area_verda_data(payload, last_modified)
            return _area_verda_data
        except Exception as exc:
            logger.warning("Could not fetch Area Verda official parking data: %s", exc)
            if cached_payload:
                payload, last_modified = cached_payload
                _area_verda_data = _build_area_verda_data(payload, last_modified)
                return _area_verda_data
            return None


def _nearest_area_verda_segments(
    data: AreaVerdaData,
    lat: float,
    lng: float,
    radius_m: int = AREA_VERDA_SEGMENT_RADIUS_M,
) -> list[tuple[float, AreaVerdaSegment]]:
    nearest: list[tuple[float, AreaVerdaSegment]] = []
    for segment in data.segments:
        if not _bbox_near(lat, lng, segment.bbox, radius_m):
            continue
        distance = _polyline_distance_m(lat, lng, segment.coordinates)
        if distance <= radius_m:
            nearest.append((distance, segment))

    nearest.sort(key=lambda item: item[0])
    return nearest


def _resident_zone_for(data: AreaVerdaData, lat: float, lng: float) -> str | None:
    for zone in data.resident_zones:
        if _bbox_near(lat, lng, zone.bbox, 0) and _point_in_polygon(lat, lng, zone.coordinates):
            return zone.code
    return None


def _dedupe_segments(
    segments: list[tuple[float, AreaVerdaSegment]],
    limit: int = AREA_VERDA_SEGMENT_LIMIT,
) -> list[tuple[float, AreaVerdaSegment]]:
    selected: list[tuple[float, AreaVerdaSegment]] = []
    seen: set[tuple[str, str | None, str | None]] = set()

    for zone_type in ("dum", "zona_verde", "zona_azul", "resident"):
        nearest_for_type = next(
            ((distance, segment) for distance, segment in segments if segment.zone_type == zone_type),
            None,
        )
        if nearest_for_type is None:
            continue
        _, segment = nearest_for_type
        key = (segment.zone_type, segment.location, segment.tariff)
        if key in seen:
            continue
        seen.add(key)
        selected.append(nearest_for_type)

    for distance, segment in segments:
        key = (segment.zone_type, segment.location, segment.tariff)
        if key in seen:
            continue
        seen.add(key)
        selected.append((distance, segment))
        if len(selected) >= limit:
            break

    return selected


def _official_segment_payload(distance: float, segment: AreaVerdaSegment) -> dict:
    return {
        "zone_type": segment.zone_type,
        "distance_m": round(distance, 1),
        "location": segment.location,
        "tariff": segment.tariff,
        "timetable": segment.timetable,
        "places": segment.places,
        "resident_zone": segment.resident_zone,
        "dum_zone": segment.dum_zone,
    }


def _zone_summary(segments: list[tuple[float, AreaVerdaSegment]], resident_zone: str | None) -> str:
    parking_zone_types = {
        segment.zone_type
        for _, segment in segments
        if segment.zone_type in {"zona_azul", "zona_verde", "resident"}
    }

    if len(parking_zone_types) > 1:
        return "mixed"
    if parking_zone_types:
        return next(iter(parking_zone_types))
    if resident_zone:
        return "resident"
    if any(segment.zone_type == "dum" for _, segment in segments):
        return "dum"
    return "unknown"


def _tariff_summary(segments: list[tuple[float, AreaVerdaSegment]]) -> tuple[str | None, str | None]:
    summaries: list[str] = []
    timetables: list[str] = []

    for _, segment in segments:
        if segment.zone_type == "dum" or not segment.tariff:
            continue
        label = segment.zone_type.replace("zona_", "Zona ").replace("_", " ").title()
        text = f"{label}: {segment.tariff}"
        if text not in summaries:
            summaries.append(text)
        if segment.timetable and segment.timetable not in timetables:
            timetables.append(segment.timetable)

    return "; ".join(summaries) or None, "; ".join(timetables) or None


async def _fetch_garages(lat: float, lng: float, radius: int = 400) -> list[dict]:
    # Case-insensitive regex (,i flag) catches OSM taggers who write "Multi-storey" etc.
    # Omit parking_entrance nodes: they include residential building entrances that are
    # not public garages and have no access tag, so they slip past the access filter.
    query = f"""
[out:json][timeout:20];
(
  node["amenity"="parking"]["parking"~"multi-storey|underground",i](around:{radius},{lat},{lng});
  way["amenity"="parking"]["parking"~"multi-storey|underground",i](around:{radius},{lat},{lng});
);
out center tags;
"""
    try:
        async with httpx.AsyncClient(timeout=25, headers=_HEADERS) as client:
            response = await client.post(OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            elements = response.json().get("elements", [])
    except Exception:
        return []

    garages = []
    seen: set[str] = set()
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("access") in ("private", "no"):
            continue
        if "center" in el:
            clat, clng = el["center"]["lat"], el["center"]["lon"]
        else:
            clat, clng = el.get("lat", lat), el.get("lon", lng)
        name = tags.get("name") or tags.get("operator") or tags.get("brand") or "Parking"
        dedup_key = f"{round(clat, 4)},{round(clng, 4)}"
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
    garages_raw, area_verda_data = await asyncio.gather(
        _fetch_garages(lat, lng),
        _get_area_verda_data(),
    )

    official_segments: list[tuple[float, AreaVerdaSegment]] = []
    resident_zone = None
    if area_verda_data:
        official_segments = _nearest_area_verda_segments(area_verda_data, lat, lng)
        resident_zone = _resident_zone_for(area_verda_data, lat, lng)

    selected_segments = _dedupe_segments(official_segments)
    zone_type = _zone_summary(official_segments, resident_zone)
    street_tariff, street_timetable = _tariff_summary(official_segments)

    nearby_unpriced: list[dict] = []
    for g in garages_raw[:3]:
        nearby_unpriced.append({
            "name": g["name"],
            "distance_m": float(g["distance_m"]),
            "monthly_est_eur": None,
        })

    parking_needed = has_car and not has_private_parking

    if has_private_parking:
        option = "private"
    elif garages_raw:
        option = "garage"
    else:
        option = "unknown"

    return {
        "has_private_parking": has_private_parking,
        # Legacy field: priced garages only. Keep it empty when prices are
        # unavailable so older frontends do not render fake monthly prices.
        "nearby_garages_count": 0,
        "nearby_garages": [],
        "nearby_garages_unpriced": nearby_unpriced,
        "nearby_garages_unpriced_count": len(nearby_unpriced),
        "zone_type": zone_type,
        "zone_monthly_eur": None,
        "street_tariff": street_tariff,
        "street_timetable": street_timetable,
        "resident_zone": resident_zone,
        "official_segments": [
            _official_segment_payload(distance, segment)
            for distance, segment in selected_segments
        ],
        "official_data_last_modified": area_verda_data.last_modified if area_verda_data else None,
        "official_source_url": AREA_VERDA_MAP_URL,
        "recommended_option": option,
        "recommended_monthly_eur": None if has_private_parking else UNVERIFIED_MONTHLY_PRICE_SENTINEL,
        "parking_needed": parking_needed,
    }
