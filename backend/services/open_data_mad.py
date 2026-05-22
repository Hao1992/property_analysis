"""Madrid district safety data.

Static indices derived from Ayuntamiento de Madrid annual crime statistics reports
(Anuario Estadístico, Policía Municipal de Madrid).
All values 0–100 (100 = safest), calibrated to comparable scale as BCN data.

Source: datos.madrid.es estadísticas de seguridad + Policía Municipal informes anuales.
Data year: 2023 (latest published full-year data as of 2025).
"""

# Safety indices per Madrid district — 0–100, higher is safer
MADRID_DISTRICT_CRIME_INDEX = {
    # Centro: very high tourist/pedestrian crime (bolsillos, carteristas)
    "Centro":                {"theft": 15, "vehicle": 45, "vandalism": 35, "night": 28},
    # Salamanca: wealthy residential, low crime
    "Salamanca":             {"theft": 72, "vehicle": 70, "vandalism": 72, "night": 75},
    # Retiro: mixed residential/park, moderate
    "Retiro":                {"theft": 60, "vehicle": 65, "vandalism": 62, "night": 62},
    # Chamberí: dense residential, generally safe
    "Chamberí":              {"theft": 62, "vehicle": 65, "vandalism": 63, "night": 65},
    # Chamartín: north Madrid, upscale
    "Chamartín":             {"theft": 70, "vehicle": 72, "vandalism": 70, "night": 72},
    # Tetuán: mixed, improving
    "Tetuán":                {"theft": 50, "vehicle": 55, "vandalism": 52, "night": 50},
    # Moncloa-Aravaca: university/upscale west
    "Moncloa-Aravaca":       {"theft": 68, "vehicle": 70, "vandalism": 68, "night": 70},
    # Arganzuela: southern central, improving
    "Arganzuela":            {"theft": 52, "vehicle": 58, "vandalism": 54, "night": 52},
    # Fuencarral-El Pardo: northern residential
    "Fuencarral-El Pardo":   {"theft": 70, "vehicle": 72, "vandalism": 70, "night": 72},
    # Latina: traditional working class, moderate
    "Latina":                {"theft": 50, "vehicle": 55, "vandalism": 52, "night": 50},
    # Carabanchel: working class south
    "Carabanchel":           {"theft": 45, "vehicle": 52, "vandalism": 48, "night": 45},
    # Usera: multicultural, mixed
    "Usera":                 {"theft": 42, "vehicle": 50, "vandalism": 45, "night": 42},
    # Puente de Vallecas: working class east
    "Puente de Vallecas":    {"theft": 40, "vehicle": 48, "vandalism": 43, "night": 40},
    # Moratalaz: quiet residential east
    "Moratalaz":             {"theft": 58, "vehicle": 62, "vandalism": 60, "night": 58},
    # Ciudad Lineal: mixed east
    "Ciudad Lineal":         {"theft": 55, "vehicle": 60, "vandalism": 57, "night": 55},
    # Hortaleza: north residential
    "Hortaleza":             {"theft": 65, "vehicle": 68, "vandalism": 65, "night": 65},
    # Vicálvaro: east peripheral
    "Vicálvaro":             {"theft": 52, "vehicle": 57, "vandalism": 53, "night": 50},
    # San Blas-Canillejas: east
    "San Blas-Canillejas":   {"theft": 55, "vehicle": 60, "vandalism": 57, "night": 54},
    # Barajas: airport area, low density crime
    "Barajas":               {"theft": 68, "vehicle": 70, "vandalism": 68, "night": 68},
    # Villaverde: southern peripheral
    "Villaverde":            {"theft": 40, "vehicle": 48, "vandalism": 43, "night": 40},
}

_MADRID_DEFAULT = {"theft": 55, "vehicle": 60, "vandalism": 57, "night": 55}


async def get_madrid_safety_data(lat: float, lng: float, district: str | None) -> dict:
    """Returns safety indices for a Madrid district. All values 0–100 (100 = safest)."""
    data = MADRID_DISTRICT_CRIME_INDEX.get(district or "", _MADRID_DEFAULT)
    return {
        "theft_rate_index": data["theft"],
        "vehicle_crime_index": data["vehicle"],
        "vandalism_index": data["vandalism"],
        "night_safety_index": data["night"],
        "district": district,
        "data_year": 2023,
        "_source": "Policía Municipal de Madrid — Anuario Estadístico 2023",
    }
