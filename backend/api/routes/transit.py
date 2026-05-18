"""Transit route detail endpoint.

Returns all stops on a given bus/metro route, including connection info at
each stop, so users can understand where a route actually goes.
"""
import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_HEADERS = {"User-Agent": "PropertyAnalyzer/2.0 (contact@propertyanalyzer.es)"}

# Barcelona bounding box
BCN_BBOX = "41.3,2.0,41.5,2.3"


@router.get("/transit/route")
async def get_route_detail(
    ref: str = Query(..., description="Route reference number, e.g. '123' or 'L3'"),
    route_type: str = Query("bus", description="Route type: bus | subway | tram | rail"),
):
    """Fetch all stops on a Barcelona transit route with connection info."""
    ref = ref.strip().upper()
    safe_ref = ref.replace('"', '').replace("'", "")

    query = f"""
[out:json][timeout:30];
relation["type"="route"]["ref"="{safe_ref}"]["route"~"^({route_type}|subway|tram|light_rail|rail)$"]({BCN_BBOX})->.routes;
.routes out body;
node(r.routes:"stop")->.stops;
node(r.routes:"platform")->.platforms;
(.stops; .platforms;) -> .all_stops;
.all_stops out body;
"""

    try:
        async with httpx.AsyncClient(timeout=35, headers=_HEADERS) as client:
            r = await client.post(OVERPASS_URL, data={"data": query})
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Overpass error: {e}")

    elements = data.get("elements", [])
    relations = [e for e in elements if e["type"] == "relation"]
    node_map  = {e["id"]: e for e in elements if e["type"] == "node"}

    if not relations:
        raise HTTPException(status_code=404, detail=f"Route '{ref}' not found in Barcelona")

    # Use the first direction (outbound)
    rel   = relations[0]
    tags  = rel.get("tags", {})

    # Extract ordered stops from relation members
    seen_names: set[str] = set()
    stops = []
    for m in rel.get("members", []):
        if m["type"] != "node":
            continue
        role = m.get("role", "")
        if role not in ("stop", "platform", "stop_entry_only", "stop_exit_only", ""):
            continue
        node = node_map.get(m["ref"])
        if not node:
            continue
        ntags = node.get("tags", {})
        name  = ntags.get("name") or ntags.get("ref") or ""
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        # Connection routes at this stop
        route_ref_raw = ntags.get("route_ref", "")
        connections: list[str] = []
        if route_ref_raw:
            import re
            connections = [r.strip() for r in re.split(r"[;,\s]+", route_ref_raw) if r.strip() and r.strip() != safe_ref]

        stops.append({
            "name":        name,
            "lat":         node["lat"],
            "lng":         node["lon"],
            "connections": connections,
        })

    # Both directions — collect second direction if present
    all_directions = []
    for rel in relations[:2]:
        rtags = rel.get("tags", {})
        direction_stops = []
        seen = set()
        for m in rel.get("members", []):
            if m["type"] != "node":
                continue
            node = node_map.get(m["ref"])
            if not node:
                continue
            name = (node.get("tags") or {}).get("name", "")
            if name and name not in seen:
                seen.add(name)
                direction_stops.append(name)
        if direction_stops:
            all_directions.append({
                "from": rtags.get("from", direction_stops[0] if direction_stops else ""),
                "to":   rtags.get("to",   direction_stops[-1] if direction_stops else ""),
                "stop_count": len(direction_stops),
            })

    return {
        "ref":        tags.get("ref", safe_ref),
        "name":       tags.get("name", ""),
        "from":       tags.get("from", ""),
        "to":         tags.get("to", ""),
        "operator":   tags.get("operator", "TMB"),
        "colour":     tags.get("colour", ""),
        "directions": all_directions,
        "stops":      stops,
        "total_stops": len(stops),
    }
