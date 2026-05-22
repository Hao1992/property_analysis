import httpx

INE_BASE = "https://servicios.ine.es/wstempus/js/ES"

# Barcelona district fallback median prices (€/m²) — 2024 market estimates
BCN_DISTRICT_MEDIAN_PPM2 = {
    "Ciutat Vella": 4800,
    "Eixample": 5200,
    "Sants-Montjuïc": 3800,
    "Les Corts": 5000,
    "Sarrià-Sant Gervasi": 6200,
    "Gràcia": 4900,
    "Horta-Guinardó": 3600,
    "Nou Barris": 3200,
    "Sant Andreu": 3500,
    "Sant Martí": 4200,
}
BCN_CITY_MEDIAN_PPM2 = 4200

# Madrid district/neighbourhood fallback prices (€/m²) — 2024 market estimates
# Source: Idealista/Fotocasa 2024 Madrid market reports
MADRID_DISTRICT_MEDIAN_PPM2 = {
    "Salamanca":        8500,
    "Retiro":           6800,
    "Chamberí":         6500,
    "Chamartín":        6200,
    "Moncloa-Aravaca":  5800,
    "Arganzuela":       4800,
    "Centro":           6000,
    "Hortaleza":        4200,
    "Fuencarral-El Pardo": 3900,
    "Latina":           3200,
    "Carabanchel":      2900,
    "Usera":            2800,
    "Puente de Vallecas": 2700,
    "Moratalaz":        3100,
    "Ciudad Lineal":    3600,
    "Vicálvaro":        2800,
    "San Blas-Canillejas": 3000,
    "Barajas":          3500,
    "Tetuán":           4500,
    "Villaverde":       2500,
}
MADRID_CITY_MEDIAN_PPM2 = 4500

# Legacy alias (kept for backward compat with callers that don't pass city)
DISTRICT_MEDIAN_PPM2 = BCN_DISTRICT_MEDIAN_PPM2


async def get_median_price_ppm2(
    census_section: str,
    district: str | None = "Eixample",
    city: str | None = None,
) -> float:
    """
    Returns median price/m² for the census section from INE.
    Falls back to district average (city-aware), then city average.
    """
    if census_section:
        try:
            url = f"{INE_BASE}/DATOS_TABLA/25171"
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url, params={"nult": 8})
                data = r.json()

            section_data = [
                d for d in data
                if str(d.get("COD", "")).startswith(census_section[:9])
                and d.get("Valor") is not None
            ]
            if section_data:
                most_recent = sorted(section_data, key=lambda x: x.get("Fecha", ""), reverse=True)[0]
                return float(most_recent["Valor"])
        except Exception:
            pass

    # City-aware district fallback
    city_key = (city or "barcelona").lower()
    if city_key == "madrid":
        return float(MADRID_DISTRICT_MEDIAN_PPM2.get(district or "", MADRID_CITY_MEDIAN_PPM2))
    # Barcelona (default)
    return float(BCN_DISTRICT_MEDIAN_PPM2.get(district or "", BCN_CITY_MEDIAN_PPM2))


async def get_census_section_from_coords(lat: float, lng: float) -> str | None:
    """
    Attempts to get census section code from INE WPS service.
    Returns 10-digit CUSEC code or None on failure.
    """
    try:
        url = "https://www2.ine.es/fuenteNomenclature/KmlWPS"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params={
                "request": "GetCapabilities",
                "lat": lat,
                "lon": lng
            })
        # Parse for CUSEC if present in response
        if "CUSEC" in r.text:
            import re
            match = re.search(r"CUSEC[\">\s:]+(\d{10})", r.text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None
