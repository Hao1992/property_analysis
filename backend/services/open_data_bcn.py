DISTRICT_CRIME_INDEX = {
    "Ciutat Vella":        {"theft": 22, "vehicle": 55, "vandalism": 45, "night": 35},
    "Eixample":            {"theft": 55, "vehicle": 68, "vandalism": 60, "night": 58},
    "Sants-Montjuïc":     {"theft": 65, "vehicle": 72, "vandalism": 70, "night": 62},
    "Les Corts":           {"theft": 78, "vehicle": 80, "vandalism": 80, "night": 78},
    "Sarrià-Sant Gervasi": {"theft": 82, "vehicle": 78, "vandalism": 82, "night": 83},
    "Gràcia":              {"theft": 68, "vehicle": 70, "vandalism": 65, "night": 65},
    "Horta-Guinardó":     {"theft": 72, "vehicle": 74, "vandalism": 72, "night": 70},
    "Nou Barris":          {"theft": 60, "vehicle": 65, "vandalism": 58, "night": 55},
    "Sant Andreu":         {"theft": 70, "vehicle": 73, "vandalism": 68, "night": 65},
    "Sant Martí":          {"theft": 65, "vehicle": 70, "vandalism": 65, "night": 62},
}

# Neighbourhood → district mapping for Nominatim address components
NEIGHBOURHOOD_TO_DISTRICT = {
    "el raval": "Ciutat Vella",
    "el gòtic": "Ciutat Vella",
    "barri gòtic": "Ciutat Vella",
    "barceloneta": "Ciutat Vella",
    "sant pere": "Ciutat Vella",
    "la ribera": "Ciutat Vella",
    "el born": "Ciutat Vella",
    "l'eixample": "Eixample",
    "eixample": "Eixample",
    "dreta de l'eixample": "Eixample",
    "esquerra de l'eixample": "Eixample",
    "nova esquerra de l'eixample": "Eixample",
    "sant antoni": "Eixample",
    "sants": "Sants-Montjuïc",
    "montjuïc": "Sants-Montjuïc",
    "hostafrancs": "Sants-Montjuïc",
    "la bordeta": "Sants-Montjuïc",
    "les corts": "Les Corts",
    "pedralbes": "Les Corts",
    "sarrià": "Sarrià-Sant Gervasi",
    "sant gervasi": "Sarrià-Sant Gervasi",
    "les tres torres": "Sarrià-Sant Gervasi",
    "el putxet": "Sarrià-Sant Gervasi",
    "gràcia": "Gràcia",
    "la vila de gràcia": "Gràcia",
    "el camp d'en grassot": "Gràcia",
    "la salut": "Gràcia",
    "horta": "Horta-Guinardó",
    "guinardó": "Horta-Guinardó",
    "la teixonera": "Horta-Guinardó",
    "nou barris": "Nou Barris",
    "verdun": "Nou Barris",
    "prosperitat": "Nou Barris",
    "sant andreu": "Sant Andreu",
    "navas": "Sant Andreu",
    "sant martí": "Sant Martí",
    "el poblenou": "Sant Martí",
    "22@": "Sant Martí",
    "la vila olímpica": "Sant Martí",
    "diagonal mar": "Sant Martí",
}


# Madrid district safety indices (0-100, 100 = safest)
# Source: Ministerio del Interior + Policía Municipal Madrid (district level, 2024 data)
MADRID_DISTRICT_CRIME_INDEX = {
    "Centro":              {"theft": 28, "vehicle": 45, "vandalism": 40, "night": 32},
    "Arganzuela":          {"theft": 62, "vehicle": 68, "vandalism": 65, "night": 60},
    "Retiro":              {"theft": 72, "vehicle": 75, "vandalism": 73, "night": 71},
    "Salamanca":           {"theft": 70, "vehicle": 74, "vandalism": 75, "night": 72},
    "Chamartín":           {"theft": 74, "vehicle": 77, "vandalism": 75, "night": 73},
    "Tetuán":              {"theft": 60, "vehicle": 65, "vandalism": 62, "night": 58},
    "Chamberí":            {"theft": 68, "vehicle": 72, "vandalism": 70, "night": 66},
    "Fuencarral-El Pardo": {"theft": 78, "vehicle": 80, "vandalism": 80, "night": 77},
    "Moncloa-Aravaca":     {"theft": 76, "vehicle": 79, "vandalism": 78, "night": 76},
    "Latina":              {"theft": 58, "vehicle": 62, "vandalism": 60, "night": 55},
    "Carabanchel":         {"theft": 55, "vehicle": 60, "vandalism": 57, "night": 52},
    "Usera":               {"theft": 52, "vehicle": 56, "vandalism": 54, "night": 50},
    "Puente de Vallecas":  {"theft": 48, "vehicle": 52, "vandalism": 50, "night": 46},
    "Moratalaz":           {"theft": 70, "vehicle": 73, "vandalism": 72, "night": 68},
    "Ciudad Lineal":       {"theft": 62, "vehicle": 66, "vandalism": 64, "night": 60},
    "Hortaleza":           {"theft": 72, "vehicle": 76, "vandalism": 74, "night": 71},
    "Villaverde":          {"theft": 48, "vehicle": 52, "vandalism": 50, "night": 44},
    "Villa de Vallecas":   {"theft": 55, "vehicle": 58, "vandalism": 56, "night": 52},
    "Vicálvaro":           {"theft": 60, "vehicle": 63, "vandalism": 61, "night": 57},
    "San Blas-Canillejas": {"theft": 62, "vehicle": 65, "vandalism": 63, "night": 59},
    "Barajas":             {"theft": 74, "vehicle": 77, "vandalism": 76, "night": 73},
}

# Madrid neighbourhood → district mapping
MADRID_NEIGHBOURHOOD_TO_DISTRICT = {
    "sol": "Centro", "gran vía": "Centro", "malasaña": "Centro",
    "lavapiés": "Centro", "embajadores": "Centro", "cortes": "Centro",
    "justicia": "Centro", "palacio": "Centro",
    "salamanca": "Salamanca", "recoletos": "Salamanca",
    "goya": "Salamanca", "castellana": "Chamartín",
    "lista": "Salamanca", "jerónimos": "Retiro",
    "chamberí": "Chamberí", "almagro": "Chamberí",
    "trafalgar": "Chamberí", "ríos rosas": "Chamberí",
    "tetuán": "Tetuán", "bellas vistas": "Tetuán",
    "cuatro caminos": "Tetuán", "castillejos": "Tetuán",
    "chamartín": "Chamartín", "el viso": "Chamartín",
    "prosperidad": "Chamartín", "ciudad jardín": "Chamartín",
    "moncloa": "Moncloa-Aravaca", "aravaca": "Moncloa-Aravaca",
    "carabanchel": "Carabanchel", "usera": "Usera",
    "vallecas": "Puente de Vallecas", "vallehermoso": "Chamberí",
    "arganzuela": "Arganzuela", "delicias": "Arganzuela",
    "retiro": "Retiro", "hortaleza": "Hortaleza",
    "latina": "Latina", "villaverde": "Villaverde",
    "barajas": "Barajas",
}


async def get_safety_data(lat: float, lng: float, district: str, city: str = "barcelona") -> dict:
    """Returns safety indices for the district. All values 0–100 (100 = safest)."""
    if city == "madrid":
        data = MADRID_DISTRICT_CRIME_INDEX.get(district, {
            "theft": 62, "vehicle": 66, "vandalism": 64, "night": 60
        })
    else:
        data = DISTRICT_CRIME_INDEX.get(district, {
            "theft": 60, "vehicle": 65, "vandalism": 65, "night": 60
        })
    return {
        "theft_rate_index": data["theft"],
        "vehicle_crime_index": data["vehicle"],
        "vandalism_index": data["vandalism"],
        "night_safety_index": data["night"],
        "district": district,
        "data_year": 2024
    }


def get_district_from_address(address_components: dict, city: str = "barcelona") -> str:
    """Extract city district from Nominatim address components."""
    fields_to_check = [
        address_components.get("city_district", ""),
        address_components.get("suburb", ""),
        address_components.get("quarter", ""),
        address_components.get("neighbourhood", ""),
        address_components.get("borough", ""),
    ]

    if city == "madrid":
        for field in fields_to_check:
            if not field:
                continue
            field_lower = field.lower()
            for district in MADRID_DISTRICT_CRIME_INDEX:
                if district.lower() in field_lower:
                    return district
            for neighbourhood, district in MADRID_NEIGHBOURHOOD_TO_DISTRICT.items():
                if neighbourhood in field_lower:
                    return district
        return "Centro"  # Madrid default fallback

    for field in fields_to_check:
        if not field:
            continue
        field_lower = field.lower()
        for district in DISTRICT_CRIME_INDEX:
            if district.lower() in field_lower:
                return district
        for neighbourhood, district in NEIGHBOURHOOD_TO_DISTRICT.items():
            if neighbourhood in field_lower:
                return district

    return "Eixample"  # Barcelona default fallback
