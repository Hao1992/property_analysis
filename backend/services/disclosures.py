"""
Pre-purchase disclosure generator.

Produces structured, actionable disclosures from analysis data —
the things buyers should know before signing that no portal shows them.

Each disclosure is: what it is + why it matters + what to do about it.
Not a score. Not a rating. A fact with context.
"""

from __future__ import annotations


def generate_disclosures(
    prop_data: dict,
    airbnb_data: dict,
    noise_data: dict,
    hidden_costs_data: dict,
    trajectory_data: dict,
    school_data: dict,
    listing_price: float | None = None,
    buyer_profile: str | None = None,
) -> list[dict]:
    items: list[dict] = []

    items += _transaction_costs(listing_price, prop_data)
    items += _airbnb_situation(airbnb_data)
    items += _building_era(prop_data)
    items += _community_debt(hidden_costs_data, prop_data)
    items += _ite_status(prop_data)
    items += _nonresident_tax(prop_data, listing_price, buyer_profile)
    items += _noise_reality(noise_data)
    items += _neighbourhood_trajectory(trajectory_data)
    items += _cedula_habitabilidad(prop_data)

    # Sort: red first, then yellow, then green/info
    _ORDER = {"red": 0, "yellow": 1, "green": 2, "info": 3}
    items.sort(key=lambda x: _ORDER.get(x["severity"], 99))
    return items


# ─── individual generators ───────────────────────────────────────────────────

def _transaction_costs(listing_price: float | None, prop_data: dict) -> list[dict]:
    cadastral = prop_data.get("cadastral_value")
    price = listing_price or (cadastral / 0.5 if cadastral else None)
    if not price:
        return [{
            "id": "transaction_costs",
            "severity": "info",
            "category": "costs",
            "title": "Add 12–14% on top of purchase price for transaction costs",
            "detail": (
                "In Catalonia, resale property buyers pay: 10% transfer tax (ITP), "
                "~1.5% notary + Land Registry, ~1% lawyer. "
                "This surprises most non-Spanish buyers who expect 5–7%."
            ),
            "action": "Budget for total transaction cost before making an offer, not after.",
        }]

    itp = price * 0.10
    notary_registry = price * 0.015
    lawyer = price * 0.01
    total_low = itp + notary_registry
    total_high = itp + notary_registry + lawyer
    pct_low = round(total_low / price * 100, 1)
    pct_high = round(total_high / price * 100, 1)

    return [{
        "id": "transaction_costs",
        "severity": "yellow",
        "category": "costs",
        "title": f"Transaction costs: ~€{int(total_low):,}–€{int(total_high):,} on top of asking price",
        "detail": (
            f"For a €{int(price):,} resale property in Catalonia: "
            f"10% ITP (€{int(itp):,}) + notary/registry (~€{int(notary_registry):,}) "
            f"+ optional but recommended lawyer (~€{int(lawyer):,}). "
            f"Total {pct_low}–{pct_high}% of purchase price. "
            "Most non-Spanish buyers underestimate this by €20,000–€40,000."
        ),
        "action": "Confirm your total budget covers purchase price + these costs before making an offer.",
    }]


def _airbnb_situation(airbnb_data: dict) -> list[dict]:
    pct = airbnb_data.get("tourist_pct_building")
    count_100m = airbnb_data.get("tourist_count_100m", 0)
    count_500m = airbnb_data.get("tourist_count_500m", 0)
    risk = airbnb_data.get("risk_label", "low")

    severity = "red" if risk in ("high", "very_high") else "yellow" if risk == "medium" else "green"

    if pct is not None:
        building_detail = (
            f"{pct:.0f}% of units in this building are registered tourist apartments"
            if pct > 0
            else "No registered tourist apartments found in this building"
        )
    else:
        building_detail = f"{count_100m} Airbnb listings within 100m"

    return [{
        "id": "airbnb_saturation",
        "severity": severity,
        "category": "neighborhood",
        "title": building_detail,
        "detail": (
            f"{count_500m} total tourist apartments within 500m. "
            "Barcelona's Constitutional Court upheld a full ban on tourist apartment licenses — "
            "all existing licenses must be relinquished by November 2028. "
            "Until then: rotating short-term neighbors, increased building wear, and potential "
            "community disputes. After 2028: this ends, which may improve residential quality "
            "but eliminates any rental income potential from tourist lets."
        ),
        "action": (
            "Before signing: verify whether the building's community has already voted to "
            "prohibit tourist rentals (building rules override individual licenses)."
            if pct and pct > 5 else None
        ),
    }]


def _building_era(prop_data: dict) -> list[dict]:
    year = prop_data.get("year_built")
    if not year:
        return []

    if 1960 <= year <= 1975:
        return [{
            "id": "building_era_risk",
            "severity": "red",
            "category": "building",
            "title": f"Built {year}: high-risk era for aluminosis",
            "detail": (
                "Barcelona buildings from 1960–1975 were frequently constructed with aluminium "
                "cement (aluminosis), which degrades over time and weakens structural elements. "
                "This cannot be detected by appearance alone — several Barcelona buildings with "
                "this problem were demolished or required costly rehabilitation."
            ),
            "action": (
                "Commission an independent structural engineer's report (ITE or informe tècnic) "
                "before signing. Do not rely on the seller's inspection."
            ),
        }]
    elif year < 1960:
        return [{
            "id": "building_era_risk",
            "severity": "yellow",
            "category": "building",
            "title": f"Built {year}: pre-1960 building — verify structural condition",
            "detail": (
                "Pre-1960 buildings may have outdated electrical wiring, lead pipes, and lack "
                "thermal insulation. Some are protected heritage buildings with restrictions "
                "on renovations. Verify the current ITE (technical building inspection) status."
            ),
            "action": "Request the building's most recent ITE report from the seller or community administrator.",
        }]
    elif 1975 < year < 1990:
        return [{
            "id": "building_era_risk",
            "severity": "yellow",
            "category": "building",
            "title": f"Built {year}: possible asbestos-containing materials",
            "detail": (
                "Buildings from 1975–1990 may contain asbestos in insulation, floor tiles, "
                "or pipes. This is only a concern during renovation work — stable asbestos "
                "is not a health risk. Budget for professional removal if you plan to renovate."
            ),
            "action": "If planning renovations, request an asbestos survey before work begins.",
        }]
    else:
        return [{
            "id": "building_era_risk",
            "severity": "green",
            "category": "building",
            "title": f"Built {year}: post-1990 construction — lower structural risk",
            "detail": (
                "Post-1990 buildings comply with modern seismic standards and are not "
                "affected by aluminosis or asbestos risks. Check the community fee includes "
                "a reserve fund (fondo de reserva) for future maintenance."
            ),
            "action": None,
        }]


def _community_debt(hidden_costs_data: dict, prop_data: dict) -> list[dict]:
    derrama = hidden_costs_data.get("derrama_risk_label", "low")
    severity = "red" if derrama == "high" else "yellow"
    derrama_detail = {
        "high": (
            "The building's derrama risk is rated HIGH based on age and condition. "
            "A large one-time community levy (derrama) may be imminent — "
            "past examples in Barcelona range from €5,000 to €40,000 per unit."
        ),
        "medium": "The building shows moderate derrama risk — a community levy is possible within the next few years.",
        "low": "Derrama risk appears low based on available data.",
    }.get(derrama, "")

    return [{
        "id": "community_debt",
        "severity": severity,
        "category": "legal",
        "title": "Unpaid community debts and levies transfer to you by law",
        "detail": (
            "In Spain, any unpaid IBI taxes and community fees (comunidad) owed by the "
            "previous owner legally become the new buyer's responsibility upon transfer — "
            "up to 4 years of IBI and the current year's community fees. "
            f"{derrama_detail}"
        ),
        "action": (
            "Before signing: request the certificado de deudas de la comunidad "
            "(community debt certificate) from the building administrator, AND the "
            "last IBI receipt proving it was paid."
        ),
    }]


def _ite_status(prop_data: dict) -> list[dict]:
    ite = prop_data.get("ite_status", "UNKNOWN")
    year = prop_data.get("year_built")
    if ite == "DESFAVORABLE":
        return [{
            "id": "ite_status",
            "severity": "red",
            "category": "building",
            "title": "Building has a UNFAVORABLE technical inspection (ITE)",
            "detail": (
                "The building's ITE (Inspecció Tècnica d'Edificis) has flagged deficiencies. "
                "This may mean mandatory rehabilitation works are pending — costs are shared "
                "among owners. You would inherit responsibility for these works upon purchase."
            ),
            "action": (
                "Request the full ITE report and understand exactly what works are required, "
                "their estimated cost, and the compliance deadline before making any offer."
            ),
        }]
    elif ite == "UNKNOWN" and year and year < 1980:
        return [{
            "id": "ite_status",
            "severity": "yellow",
            "category": "building",
            "title": "Building inspection (ITE) status could not be confirmed",
            "detail": (
                f"This {year} building is old enough to require periodic ITE inspections. "
                "We could not confirm the current inspection status from available data."
            ),
            "action": "Ask the seller or building administrator for the most recent ITE report.",
        }]
    return []


def _nonresident_tax(
    prop_data: dict,
    listing_price: float | None,
    buyer_profile: str | None,
) -> list[dict]:
    is_expat = buyer_profile in ("expat", None)  # default to showing for unknown profile
    if not is_expat:
        return []

    cadastral = prop_data.get("cadastral_value")
    if not cadastral and listing_price:
        cadastral = listing_price * 0.5  # rough proxy

    if not cadastral:
        return [{
            "id": "nonresident_tax",
            "severity": "info",
            "category": "costs",
            "title": "Non-resident owners pay annual income tax even with no rental income",
            "detail": (
                "If you are not a Spanish tax resident, you must file and pay IRNR "
                "(Impuesto sobre la Renta de No Residentes) annually — typically 1.1% "
                "of the cadastral value, even if the property sits empty. "
                "This is separate from IBI and is frequently overlooked by foreign buyers."
            ),
            "action": "Consult a Spanish gestor or tax advisor before purchase to understand your annual tax obligation.",
        }]

    annual_irnr = round(cadastral * 0.011)
    return [{
        "id": "nonresident_tax",
        "severity": "yellow",
        "category": "costs",
        "title": f"Non-resident tax: ~€{annual_irnr:,}/year even if property sits empty",
        "detail": (
            f"Based on cadastral value (€{int(cadastral):,}), estimated IRNR = "
            f"€{annual_irnr:,}/year (1.1% × cadastral value). "
            "This applies to all non-Spanish tax residents and is due regardless of "
            "whether you rent the property or leave it vacant. "
            "Plus IBI on top."
        ),
        "action": "Factor this into your annual holding cost. Register with a Spanish tax representative (representante fiscal) within 30 days of purchase.",
    }]


def _noise_reality(noise_data: dict) -> list[dict]:
    night = noise_data.get("night_noise_score", 100)
    bars = noise_data.get("bars_clubs_500m", 0)
    nightclubs = noise_data.get("nightclubs_500m", 0)

    if night < 40 or bars > 10 or nightclubs > 2:
        return [{
            "id": "noise_reality",
            "severity": "red",
            "category": "neighborhood",
            "title": f"High noise risk: {bars} bars/clubs within 500m, {nightclubs} nightclubs",
            "detail": (
                "This area has significant late-night activity. "
                "Property listings never disclose noise levels — but it's one of the top "
                "causes of buyer regret. Noise through walls and windows is not apparent "
                "during a daytime viewing."
            ),
            "action": (
                "Visit the property on a Friday or Saturday night after 22:00 before committing. "
                "Ask specifically about double-glazing and insulation quality."
            ),
        }]
    elif night < 65 or bars > 5:
        return [{
            "id": "noise_reality",
            "severity": "yellow",
            "category": "neighborhood",
            "title": f"Moderate noise environment: {bars} bars/clubs within 500m",
            "detail": (
                "The area has moderate nightlife activity. Whether this is a problem "
                "depends heavily on your floor, the building's insulation, and your tolerance. "
                "It is not visible from a daytime viewing."
            ),
            "action": "Visit at night before making an offer.",
        }]
    return []


def _neighbourhood_trajectory(trajectory_data: dict) -> list[dict]:
    trend = trajectory_data.get("trend", "stable")
    new_biz = trajectory_data.get("new_businesses_12m", 0)
    permits = trajectory_data.get("renovation_permits_12m", 0)

    if trend == "declining":
        return [{
            "id": "neighbourhood_trajectory",
            "severity": "yellow",
            "category": "neighborhood",
            "title": "Neighbourhood showing declining business activity",
            "detail": (
                f"Over the past 12 months: {new_biz} new business licences, "
                f"{permits} renovation permits — indicators of a cooling or declining area. "
                "This affects future resale liquidity and quality of local services."
            ),
            "action": "Research why the area is declining before committing — development plans, tenant pressures, or seasonal patterns?",
        }]
    elif trend == "rising":
        return [{
            "id": "neighbourhood_trajectory",
            "severity": "green",
            "category": "neighborhood",
            "title": "Neighbourhood showing active growth",
            "detail": (
                f"{new_biz} new business licences and {permits} renovation permits in 12 months "
                "signal a rising area. This is a positive indicator for long-term value."
            ),
            "action": None,
        }]
    return []


def _cedula_habitabilidad(prop_data: dict) -> list[dict]:
    year = prop_data.get("year_built")
    if year and year < 1995:
        return [{
            "id": "cedula_habitabilidad",
            "severity": "yellow",
            "category": "legal",
            "title": "Verify cèdula d'habitabilitat is current before signing",
            "detail": (
                "The cèdula d'habitabilitat (habitation certificate) is required in Catalonia "
                "to connect utilities (electricity, water, gas) and to legally rent the property. "
                f"This {year} building predates the current certification system — the certificate "
                "may have expired or never been renewed. Obtaining a new one costs €300–€800 "
                "and requires a technical inspection; some properties fail."
            ),
            "action": (
                "Ask the seller to provide a valid cèdula d'habitabilitat — it must be current. "
                "If it expired, factor in the renewal cost and risk."
            ),
        }]
    return []
