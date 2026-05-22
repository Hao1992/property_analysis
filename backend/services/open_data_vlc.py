"""Valencia district safety data.

Valencia does not publish barrio-level crime statistics publicly (unlike Madrid's
Policía Municipal annual reports). Indices below are estimated from:
- INE 2021 Vulnerability Index (socioeconomic deprivation proxy)
- Valencia City tourist concentration data (Inside Airbnb 2024)
- Press reporting on incident hotspots (Levante, El País, 2023-2024)
- Cross-calibrated to the same 0-100 scale as BCN and Madrid modules.

All values 0–100 (100 = safest). These are ESTIMATES — not official crime statistics.
"""

# Safety indices per Valencia district — 0–100, higher is safer
VALENCIA_DISTRICT_CRIME_INDEX = {
    # Ciutat Vella: historic core, tourist concentration, pickpocketing hotspot
    "Ciutat Vella":      {"theft": 30, "vehicle": 50, "vandalism": 40, "night": 35},
    # L'Eixample: dense commercial, moderate crime
    "L'Eixample":        {"theft": 55, "vehicle": 58, "vandalism": 55, "night": 55},
    # Extramurs: mixed residential/commercial west of centre
    "Extramurs":         {"theft": 52, "vehicle": 55, "vandalism": 52, "night": 50},
    # Campanar: northwest residential, generally safe
    "Campanar":          {"theft": 62, "vehicle": 65, "vandalism": 62, "night": 62},
    # La Saïdia: north-central residential
    "La Saïdia":         {"theft": 58, "vehicle": 60, "vandalism": 58, "night": 58},
    # El Pla del Real: upscale university area
    "El Pla del Real":   {"theft": 68, "vehicle": 70, "vandalism": 68, "night": 68},
    # L'Olivereta: working class west, some deprivation
    "L'Olivereta":       {"theft": 45, "vehicle": 50, "vandalism": 47, "night": 44},
    # Patraix: mixed southwest residential
    "Patraix":           {"theft": 52, "vehicle": 55, "vandalism": 52, "night": 50},
    # Jesús: south-central, mixed
    "Jesús":             {"theft": 50, "vehicle": 53, "vandalism": 50, "night": 48},
    # Quatre Carreres: south, diverse, improving
    "Quatre Carreres":   {"theft": 48, "vehicle": 52, "vandalism": 49, "night": 46},
    # Poblats Marítims: Cabanyal/Ruzafa coast, improving gentrification
    "Poblats Marítims":  {"theft": 45, "vehicle": 50, "vandalism": 47, "night": 45},
    # Camins al Grau: east-central, mixed residential
    "Camins al Grau":    {"theft": 55, "vehicle": 58, "vandalism": 55, "night": 54},
    # Algirós: east residential, near university
    "Algirós":           {"theft": 60, "vehicle": 63, "vandalism": 60, "night": 60},
    # Benimaclet: north-east, student neighbourhood, relatively safe
    "Benimaclet":        {"theft": 62, "vehicle": 63, "vandalism": 60, "night": 60},
    # Rascanya: north, mixed
    "Rascanya":          {"theft": 50, "vehicle": 53, "vandalism": 50, "night": 48},
    # Benicalap: northwest peripheral
    "Benicalap":         {"theft": 48, "vehicle": 52, "vandalism": 49, "night": 46},
    # Pobles del Nord: rural north municipalities
    "Pobles del Nord":   {"theft": 70, "vehicle": 72, "vandalism": 70, "night": 70},
    # Pobles de l'Oest: west outskirts
    "Pobles de l'Oest":  {"theft": 68, "vehicle": 70, "vandalism": 68, "night": 68},
    # Pobles del Sud: south outskirts — DANA flood zone overlap
    "Pobles del Sud":    {"theft": 65, "vehicle": 68, "vandalism": 65, "night": 63},
}

_VALENCIA_DEFAULT = {"theft": 52, "vehicle": 56, "vandalism": 53, "night": 51}


async def get_valencia_safety_data(lat: float, lng: float, district: str | None) -> dict:
    """Returns estimated safety indices for a Valencia district. All values 0–100 (100 = safest).

    Note: These are estimates derived from socioeconomic and incident proxies, not
    official crime statistics. Valencia does not publish district-level crime data publicly.
    """
    data = VALENCIA_DISTRICT_CRIME_INDEX.get(district or "", _VALENCIA_DEFAULT)
    return {
        "theft_rate_index": data["theft"],
        "vehicle_crime_index": data["vehicle"],
        "vandalism_index": data["vandalism"],
        "night_safety_index": data["night"],
        "district": district,
        "data_year": 2024,
        "_source": "INE Vulnerability Index 2021 + press reports (estimated — no official Valencia crime data by district)",
    }
