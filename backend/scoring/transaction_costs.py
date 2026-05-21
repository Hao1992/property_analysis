"""Transaction cost calculations.

Two functions:
  calculate_acquisition_costs  — buyer's total cash needed
  estimate_seller_economics    — seller's costs → floor price / negotiation headroom
"""
from __future__ import annotations
from typing import Optional

_CATALUNYA_ITP_RATE = 0.10
_MADRID_ITP_RATE    = 0.06
_IVA_RATE = 0.10
_AJD_RATE_CATALUNYA = 0.015
_AJD_RATE_MADRID    = 0.0075

_LAND_FRACTION = 0.35
_PLUSVALIA_BASE_COEFF_10YR = 0.17  # objective method, ~10 years
_PLUSVALIA_TAX_RATE_BCN  = 0.28    # Barcelona tipo de gravamen
_PLUSVALIA_TAX_RATE_MAD  = 0.29    # Madrid tipo de gravamen


def calculate_acquisition_costs(
    listing_price: float,
    is_new_build: bool = False,
    city: str = "barcelona",
    buyer_type: str = "resident",
) -> dict:
    """Return itemized acquisition costs for a buyer in the given city."""
    is_madrid = city == "madrid"
    itp_rate  = _MADRID_ITP_RATE if is_madrid else _CATALUNYA_ITP_RATE
    ajd_rate  = _AJD_RATE_MADRID if is_madrid else _AJD_RATE_CATALUNYA
    region_label = "Madrid" if is_madrid else "Catalunya"

    if is_new_build:
        transfer_tax = round(listing_price * _IVA_RATE)
        ajd = round(listing_price * ajd_rate)
        ajd_pct = int(ajd_rate * 100) if ajd_rate == int(ajd_rate) else ajd_rate * 100
        transfer_tax_label = f"IVA (10%) + AJD ({ajd_rate*100:.2g}%)"
        transfer_total = transfer_tax + ajd
    else:
        transfer_tax = round(listing_price * itp_rate)
        transfer_tax_label = f"ITP ({int(itp_rate*100)}%, {region_label})"
        transfer_total = transfer_tax
        ajd = 0

    # Notary + registry + gestoría: rough scale based on transaction amount
    notary_est = min(2500, max(700, round(listing_price * 0.0015 + 600)))
    registry_est = min(1500, max(300, round(listing_price * 0.0006 + 200)))
    gestoria_est = 350
    other_fees = notary_est + registry_est + gestoria_est

    total = round(listing_price + transfer_total + other_fees)
    overhead_pct = round((total - listing_price) / listing_price * 100, 1)

    # Minimum savings: residents up to 80% LTV (20% down); non-residents max 60-70% LTV (30-40% down)
    min_down_pct = 0.30 if buyer_type == "non_resident" else 0.20
    min_down = round(listing_price * min_down_pct)
    min_savings = round(min_down + transfer_total + other_fees)

    return {
        "listing_price":      round(listing_price),
        "is_new_build":       is_new_build,
        "transfer_tax":       transfer_total,
        "transfer_tax_label": transfer_tax_label,
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
    city: str = "barcelona",
) -> dict:
    """Estimate seller's transaction costs to derive floor price and negotiation room."""
    agency_low  = round(listing_price * 0.03)
    agency_high = round(listing_price * 0.05)

    tax_rate = _PLUSVALIA_TAX_RATE_MAD if city == "madrid" else _PLUSVALIA_TAX_RATE_BCN

    plusvalia_est: Optional[int] = None
    if cadastral_value and cadastral_value > 0:
        land_value = cadastral_value * _LAND_FRACTION
        coeff = min(_PLUSVALIA_BASE_COEFF_10YR * (years_owned_est / 10), 0.45)
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
