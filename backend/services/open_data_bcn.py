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


async def get_safety_data(lat: float, lng: float, district: str) -> dict:
    """Returns safety indices for the district. All values 0–100 (100 = safest)."""
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


def get_district_from_address(address_components: dict) -> str:
    """Extract Barcelona district from Nominatim address components."""
    fields_to_check = [
        address_components.get("city_district", ""),
        address_components.get("suburb", ""),
        address_components.get("quarter", ""),
        address_components.get("neighbourhood", ""),
    ]

    for field in fields_to_check:
        if not field:
            continue
        field_lower = field.lower()

        # Direct district name match
        for district in DISTRICT_CRIME_INDEX:
            if district.lower() in field_lower:
                return district

        # Neighbourhood → district mapping
        for neighbourhood, district in NEIGHBOURHOOD_TO_DISTRICT.items():
            if neighbourhood in field_lower:
                return district

    return "Eixample"  # Default fallback
