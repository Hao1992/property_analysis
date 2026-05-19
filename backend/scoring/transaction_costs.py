"""Transaction cost calculations.

Two functions:
  calculate_acquisition_costs  — buyer's total cash needed
  estimate_seller_economics    — seller's costs → floor price / negotiation headroom
"""
from __future__ import annotations
from typing import Optional

_CATALUNYA_ITP_RATE = 0.10
_IVA_RATE = 0.10
_AJD_RATE_CATALUNYA = 0.015

_LAND_FRACTION = 0.35
_PLUSVALIA_BASE_COEFF_10YR = 0.17  # Barcelona objective method, ~10 years
_PLUSVALIA_TAX_RATE = 0.28         # Barcelona tipo de gravamen


def calculate_acquisition_costs(
    listing_price: float,
    is_new_build: bool = False,
) -> dict:
    """Return itemized acquisition costs for a buyer in Catalunya."""
    if is_new_build:
        transfer_tax = round(listing_price * _IVA_RATE)
        ajd = round(listing_price * _AJD_RATE_CATALUNYA)
        transfer_tax_label = "IVA (10%) + AJD (1.5%)"
        transfer_total = transfer_tax + ajd
    else:
        transfer_tax = round(listing_price * _CATALUNYA_ITP_RATE)
        transfer_tax_label = "ITP (10%, Catalunya)"
        transfer_total = transfer_tax
        ajd = 0

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
) -> dict:
    """Estimate seller's transaction costs to derive floor price and negotiation room."""
    agency_low  = round(listing_price * 0.03)
    agency_high = round(listing_price * 0.05)

    plusvalia_est: Optional[int] = None
    if cadastral_value and cadastral_value > 0:
        land_value = cadastral_value * _LAND_FRACTION
        coeff = min(_PLUSVALIA_BASE_COEFF_10YR * (years_owned_est / 10), 0.45)
        plusvalia_est = round(land_value * coeff * _PLUSVALIA_TAX_RATE)

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
