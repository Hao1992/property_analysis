import httpx
import xml.etree.ElementTree as ET
import logging

CATASTRO_BASE = "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC"
NS = {"ns": "http://www.catastro.meh.es/"}
log = logging.getLogger(__name__)

# ~45m offsets in degrees at Barcelona latitude (41°N)
# 0.0004° lat ≈ 44m, 0.0005° lng ≈ 38m
_GRID_OFFSETS = [
    (0, 0),
    (0.0004, 0), (-0.0004, 0),
    (0, 0.0005), (0, -0.0005),
    (0.0004, 0.0005), (0.0004, -0.0005),
    (-0.0004, 0.0005), (-0.0004, -0.0005),
]


async def get_property_data(lat: float, lng: float) -> dict:
    """
    Returns cadastral data for the parcel at given coordinates.
    Tries a 3×3 grid of nearby coordinates because Nominatim often returns
    street centroids that fall outside the specific building parcel.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        for dlat, dlng in _GRID_OFFSETS:
            result = await _try_coords(client, lat + dlat, lng + dlng)
            if result is not None:
                result["lat"] = lat   # always return original coords
                result["lng"] = lng
                if dlat != 0 or dlng != 0:
                    log.debug("Catastro: hit at offset (%.4f, %.4f) from original", dlat, dlng)
                return result

    log.warning("Catastro: no parcel found near (%.5f, %.5f) after grid search", lat, lng)
    return _empty_property(lat, lng)


async def _try_coords(client: httpx.AsyncClient, lat: float, lng: float) -> dict | None:
    """Try a single coordinate pair. Returns property dict or None on miss."""
    try:
        r = await client.get(
            f"{CATASTRO_BASE}/OVCCoordenadas.asmx/Consulta_RCCOOR",
            params={"SRS": "EPSG:4326", "Coordenada_X": lng, "Coordenada_Y": lat},
        )
        root = ET.fromstring(r.text)

        # Error code 16 = no parcel at these coords — try next offset
        err = root.findtext(".//ns:cod", namespaces=NS)
        if err == "16":
            return None

        rc_el = root.find(".//ns:rc", NS)
        if rc_el is None or not rc_el.text:
            return None

        rc = rc_el.text.strip()

        r2 = await client.get(
            f"{CATASTRO_BASE}/OVCCallejero.asmx/Consulta_DNPRC",
            params={"Provincia": "", "Municipio": "", "RC": rc},
        )
        root2 = ET.fromstring(r2.text)

        year_built = _int(root2.findtext(".//ns:ant", namespaces=NS))
        surface    = _float(root2.findtext(".//ns:sfc", namespaces=NS))
        cad_value  = _float(root2.findtext(".//ns:vcat", namespaces=NS))
        address    = root2.findtext(".//ns:ldt", namespaces=NS)

        # Only accept if we got at least one useful field
        if year_built is None and surface is None and cad_value is None:
            return None

        return {
            "rc":                 rc,
            "surface_m2":         surface,
            "year_built":         year_built,
            "use":                root2.findtext(".//ns:luso", namespaces=NS),
            "address_normalized": address or f"{lat:.5f},{lng:.5f}",
            "cadastral_value":    cad_value,
            "lat": lat,
            "lng": lng,
        }

    except Exception as exc:
        log.debug("Catastro error at (%.5f, %.5f): %s", lat, lng, exc)
        return None


def _empty_property(lat: float, lng: float) -> dict:
    return {
        "rc": None, "surface_m2": None, "year_built": None,
        "use": None, "address_normalized": f"{lat:.5f}, {lng:.5f}",
        "cadastral_value": None, "lat": lat, "lng": lng,
    }


def _float(val):
    try:
        return float(val) if val else None
    except Exception:
        return None


def _int(val):
    try:
        return int(val) if val else None
    except Exception:
        return None
