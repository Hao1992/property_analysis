import httpx
import xml.etree.ElementTree as ET

CATASTRO_BASE = "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC"
NS = {"ns": "http://www.catastro.meh.es/"}


async def get_property_data(lat: float, lng: float) -> dict:
    """Returns cadastral data for the parcel at given coordinates."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{CATASTRO_BASE}/OVCCoordenadas.asmx/Consulta_RCCOOR",
                params={"SRS": "EPSG:4326", "Coordenada_X": lng, "Coordenada_Y": lat}
            )
            root = ET.fromstring(r.text)
            rc_el = root.find(".//ns:rc", NS)
            if rc_el is None or not rc_el.text:
                return _empty_property(lat, lng)

            rc = rc_el.text.strip()

            r2 = await client.get(
                f"{CATASTRO_BASE}/OVCCallejero.asmx/Consulta_DNPRC",
                params={"Provincia": "", "Municipio": "", "RC": rc}
            )
            root2 = ET.fromstring(r2.text)

        return {
            "rc": rc,
            "surface_m2": _float(root2.findtext(".//ns:sfc", namespaces=NS)),
            "year_built":  _int(root2.findtext(".//ns:ant", namespaces=NS)),
            "use":         root2.findtext(".//ns:luso", namespaces=NS),
            "address_normalized": root2.findtext(".//ns:ldt", namespaces=NS) or f"{lat},{lng}",
            "cadastral_value": _float(root2.findtext(".//ns:vcat", namespaces=NS)),
            "lat": lat,
            "lng": lng,
        }
    except Exception:
        return _empty_property(lat, lng)


def _empty_property(lat: float, lng: float) -> dict:
    return {
        "rc": None,
        "surface_m2": None,
        "year_built": None,
        "use": None,
        "address_normalized": f"{lat:.5f}, {lng:.5f}",
        "cadastral_value": None,
        "lat": lat,
        "lng": lng,
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
