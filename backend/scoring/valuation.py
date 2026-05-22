ENERGY_MULT = {"A": 1.08, "B": 1.04, "C": 1.01, "D": 1.00, "E": 0.96, "F": 0.91, "G": 0.85}
FLOOR_MULT  = {0: 0.97, 1: 1.00, 2: 1.00, 3: 1.01, 4: 1.02, 5: 1.03}

FEATURE_MULTS = {
    "has_lift":    1.02,
    "has_terrace": 1.03,
    "has_parking": 1.05,
    "has_views":   1.06,
    "renovated":   1.04,
}
FEATURE_LABELS = {
    "has_lift":    "Lift",
    "has_terrace": "Terrace/balcony",
    "has_parking": "Parking included",
    "has_views":   "Sea/park views",
    "renovated":   "Recently renovated",
}


def estimate_fair_value(
    median_ppm2: float,
    prop: dict,
    listing_price: float | None = None
) -> dict:
    _surface_known = prop.get("surface_m2") is not None
    surface = prop.get("surface_m2") or 80
    base = median_ppm2 * surface
    adjustments = []

    # Age adjustment
    year = prop.get("year_built")
    if year:
        age = 2025 - year
        age_mult = (
            1.05 if age < 10 else
            1.02 if age < 30 else
            1.00 if age < 50 else
            0.96 if age < 70 else
            0.91
        )
        ite_bonus = 0.04 if prop.get("ite_status") == "FAVORABLE" and age > 40 else 0
        final_age_mult = age_mult + ite_bonus
        adjustments.append({
            "name": f"Building age ({age} yrs)",
            "multiplier": round(final_age_mult, 3),
            "impact_eur": round(base * (final_age_mult - 1)),
            "source": "Catastro"
        })

    # Energy certificate
    cert = (prop.get("energy_cert") or "D").upper()
    e_mult = ENERGY_MULT.get(cert, 1.00)
    adjustments.append({
        "name": f"Energy cert {cert}",
        "multiplier": e_mult,
        "impact_eur": round(base * (e_mult - 1)),
        "source": "Catastro"
    })

    # Floor level
    floor = prop.get("floor") or 3
    f_mult = FLOOR_MULT.get(min(floor, 5), 1.04 if floor <= 9 else 1.06)
    adjustments.append({
        "name": f"Floor level ({'Ground' if floor == 0 else 'F' + str(floor)})",
        "multiplier": f_mult,
        "impact_eur": round(base * (f_mult - 1)),
        "source": "Catastro"
    })

    # Optional features
    for key, mult in FEATURE_MULTS.items():
        if prop.get(key):
            adjustments.append({
                "name": FEATURE_LABELS[key],
                "multiplier": mult,
                "impact_eur": round(base * (mult - 1)),
                "source": "listing"
            })

    total_adj = sum(a["impact_eur"] for a in adjustments)
    fair_value = round(base + total_adj)
    fair_ppm2 = round(fair_value / surface)

    # Confidence score
    conf = 0.50
    if prop.get("year_built"):    conf += 0.10
    if prop.get("energy_cert"):   conf += 0.07
    if prop.get("surface_m2"):    conf += 0.08
    if prop.get("ite_status") not in (None, "UNKNOWN"): conf += 0.10
    conf = min(0.85, conf)

    result = {
        "base_value":       round(base),
        "fair_value":       fair_value,
        "fair_value_low":   round(fair_value * 0.88),
        "fair_value_high":  round(fair_value * 1.12),
        "fair_value_ppm2":  fair_ppm2,
        "adjustments":      adjustments,
        "confidence":       round(conf, 2),
        "verdict":          "fair",
        "vs_listing_pct":   None,
    }

    if listing_price:
        delta_pct = ((listing_price - fair_value) / fair_value) * 100
        # Only show vs_listing_pct and verdict when surface is known.
        # With 80m² fallback, a Pedralbes villa at €900k falsely shows "+123% overpriced".
        if _surface_known:
            result["vs_listing_pct"] = round(delta_pct, 1)
            result["verdict"] = (
                "significantly_overpriced" if delta_pct > 15 else
                "overpriced"               if delta_pct > 5  else
                "fair"                     if delta_pct >= -5 else
                "undervalued"
            )
            result["price_fairness_score"] = (
                20  if delta_pct > 25 else
                40  if delta_pct > 15 else
                60  if delta_pct > 5  else
                80  if delta_pct >= -5 else
                100
            )
        else:
            # Surface unknown → price comparison unreliable; suppress verdict
            result["vs_listing_pct"] = None
            result["verdict"] = "unknown"
            result["price_fairness_score"] = None
            result["_surface_assumed_m2"] = 80  # flag for UI to show disclaimer

    return result
