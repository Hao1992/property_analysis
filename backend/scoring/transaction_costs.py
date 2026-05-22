"""Transaction cost calculations — city-aware.

Two functions:
  calculate_acquisition_costs  — buyer's total cash needed
  estimate_seller_economics    — seller's costs → floor price / negotiation headroom

Supported cities: "barcelona" (Catalunya ITP), "madrid" (Madrid ITP), "valencia" (CV ITP)
Default (None) falls back to Catalunya rates for backward compat.
"""
from __future__ import annotations
from typing import Optional

_IVA_RATE = 0.10

# AJD (Actos Jurídicos Documentados) for new builds only
_AJD_RATES = {
    "barcelona": 0.015,   # Catalunya: 1.5%
    "madrid":    0.0075,  # Comunidad de Madrid: 0.75%
    "valencia":  0.015,   # Comunitat Valenciana: 1.5%
}

# IBI municipal property tax rates (% of cadastral value, annual)
IBI_RATES = {
    "barcelona": 0.0066,   # Barcelona municipality (Ajuntament 2024)
    "madrid":    0.00456,  # Madrid municipality (Ayuntamiento 2024)
    "valencia":  0.005784, # Valencia municipality (Ayuntamiento de Valencia 2024)
}
IBI_RATE_DEFAULT = 0.0066  # fall back to Barcelona if city unknown

# Plusvalía: land fraction for urban flats (suelo % of cadastral), BCN tipo de gravamen
_LAND_FRACTION = 0.65        # urban BCN/MAD/VLC: ~65% of cadastral is land value
_PLUSVALIA_TAX_RATES = {
    "barcelona": 0.30,   # BCN tipo de gravamen (2024)
    "madrid":    0.29,   # Madrid tipo de gravamen (2024)
    "valencia":  0.297,  # Valencia Ayuntamiento tipo de gravamen (2024, max 30%)
}
_PLUSVALIA_TAX_RATE_DEFAULT = 0.30

# RDL 26/2021 objective method coefficients by years_owned
# Official table: years 1→20 (beyond 20 capped at 0.45)
_PLUSVALIA_COEFFS = {
    1: 0.14, 2: 0.13, 3: 0.12, 4: 0.12, 5: 0.11,
    6: 0.11, 7: 0.10, 8: 0.10, 9: 0.09, 10: 0.08,
    11: 0.08, 12: 0.08, 13: 0.08, 14: 0.08, 15: 0.08,
    16: 0.08, 17: 0.08, 18: 0.08, 19: 0.07, 20: 0.07,
}


def _plusvalia_coeff(years: int) -> float:
    """Return RDL 26/2021 objective method coefficient for given years of ownership."""
    if years <= 0:
        return 0.14
    if years >= 20:
        return 0.45
    return _PLUSVALIA_COEFFS.get(years, 0.08)


def _catalunya_itp_progressive(price: float) -> tuple[float, str]:
    """
    DL 5/2025 Catalunya progressive ITP brackets (resale), per atc.gencat.cat:
      ≤ €600,000:               10%  (flat)
      €600,001 – €900,000:      11%
      €900,001 – €1,500,000:    12%
      > €1,500,000:             13%
    Returns (tax_amount, label).
    """
    if price <= 600_000:
        tax = price * 0.10
        label = "ITP (10%, Catalunya)"
    elif price <= 900_000:
        tax = 600_000 * 0.10 + (price - 600_000) * 0.11
        eff = round(tax / price * 100, 1)
        label = f"ITP (10–11%, Catalunya, efectivo {eff}%)"
    elif price <= 1_500_000:
        tax = 600_000 * 0.10 + 300_000 * 0.11 + (price - 900_000) * 0.12
        eff = round(tax / price * 100, 1)
        label = f"ITP (10–12%, Catalunya, efectivo {eff}%)"
    else:
        tax = 600_000 * 0.10 + 300_000 * 0.11 + 600_000 * 0.12 + (price - 1_500_000) * 0.13
        eff = round(tax / price * 100, 1)
        label = f"ITP (10–13%, Catalunya, efectivo {eff}%)"
    return round(tax), label


def calculate_acquisition_costs(
    listing_price: float,
    is_new_build: bool = False,
    city: str | None = None,
) -> dict:
    """Return itemized acquisition costs for a buyer. city: 'barcelona' | 'madrid' | None."""
    city_key = (city or "barcelona").lower()

    if is_new_build:
        transfer_tax = round(listing_price * _IVA_RATE)
        ajd_rate = _AJD_RATES.get(city_key, _AJD_RATES["barcelona"])
        ajd = round(listing_price * ajd_rate)
        ajd_pct = round(ajd_rate * 100, 2)
        transfer_tax_label = f"IVA (10%) + AJD ({ajd_pct}%, {city_key.capitalize()})"
        transfer_total = transfer_tax + ajd
    else:
        ajd = 0
        if city_key == "madrid":
            transfer_tax = round(listing_price * 0.06)
            transfer_tax_label = "ITP (6%, Comunidad de Madrid)"
            transfer_total = transfer_tax
        elif city_key == "valencia":
            transfer_tax = round(listing_price * 0.10)
            transfer_tax_label = "ITP (10%, Comunitat Valenciana)"
            transfer_total = transfer_tax
        else:
            # Catalunya progressive
            transfer_tax, transfer_tax_label = _catalunya_itp_progressive(listing_price)
            transfer_total = transfer_tax

    # Notary + registry + gestoría: rough scale based on transaction amount
    notary_est = min(2500, max(700, round(listing_price * 0.0015 + 600)))
    registry_est = min(1500, max(300, round(listing_price * 0.0006 + 200)))
    gestoria_est = 350
    other_fees = notary_est + registry_est + gestoria_est

    total = round(listing_price + transfer_total + other_fees)
    overhead_pct = round((total - listing_price) / listing_price * 100, 1)

    # Minimum savings: 20% down (bank finances up to 80%) + all purchase costs
    min_down = round(listing_price * 0.20)
    min_savings = round(min_down + transfer_total + other_fees)

    return {
        "listing_price":      round(listing_price),
        "is_new_build":       is_new_build,
        "transfer_tax":       transfer_total,
        "transfer_tax_label": transfer_tax_label,
        "ajd":                ajd,
        "notary_est":         notary_est,
        "registry_est":       registry_est,
        "gestoria_est":       gestoria_est,
        "other_fees":         other_fees,
        "total":              total,
        "overhead_pct":       overhead_pct,
        "min_down_payment":   min_down,
        "min_savings_needed": min_savings,
    }


def estimate_seller_economics(
    listing_price: float,
    cadastral_value: Optional[float] = None,
    years_owned_est: int = 10,
    city: str | None = None,
) -> dict:
    """Estimate seller's transaction costs to derive floor price and negotiation room."""
    city_key = (city or "barcelona").lower()
    agency_low  = round(listing_price * 0.03)
    agency_high = round(listing_price * 0.05)

    plusvalia_est: Optional[int] = None
    if cadastral_value and cadastral_value > 0:
        land_value = cadastral_value * _LAND_FRACTION
        coeff = _plusvalia_coeff(years_owned_est)
        tax_rate = _PLUSVALIA_TAX_RATES.get(city_key, _PLUSVALIA_TAX_RATE_DEFAULT)
        plusvalia_est = round(land_value * coeff * tax_rate)

    energy_cert_cost = 200  # mandatory, roughly €150–300

    extra = (plusvalia_est or 0) + energy_cert_cost
    seller_costs_low  = agency_low  + extra
    seller_costs_high = agency_high + extra

    return {
        "listing_price":             round(listing_price),
        "agency_low":                agency_low,
        "agency_high":               agency_high,
        "plusvalia_est":             plusvalia_est,
        "years_owned_est":           years_owned_est,
        "energy_cert_cost":          energy_cert_cost,
        "seller_costs_low":          seller_costs_low,
        "seller_costs_high":         seller_costs_high,
        "seller_floor_low":          round(listing_price - seller_costs_high),
        "seller_floor_high":         round(listing_price - seller_costs_low),
        "negotiation_headroom_pct":  round(seller_costs_high / listing_price * 100, 1),
    }
