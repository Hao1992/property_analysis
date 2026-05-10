import httpx

INE_BASE = "https://servicios.ine.es/wstempus/js/ES"

# Barcelona district fallback median prices (€/m²) — 2024 estimates
DISTRICT_MEDIAN_PPM2 = {
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


async def get_median_price_ppm2(census_section: str, district: str = "Eixample") -> float:
    """
    Returns median price/m² for the census section from INE.
    Falls back to district average, then Barcelona city average (4200 €/m²).
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

    # District fallback
    return float(DISTRICT_MEDIAN_PPM2.get(district, 4200))


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
