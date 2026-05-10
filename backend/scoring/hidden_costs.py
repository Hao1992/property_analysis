"""Hidden cost estimator: annual holding costs beyond the mortgage.

All figures are estimates based on Barcelona averages and property attributes.
No external API calls — derived from Catastro data already fetched.

score_hidden_costs() now accepts prop to derive energy_future from the actual
cert letter (graduated scale) rather than a binary upgrade-required flag.
"""
from __future__ import annotations


def estimate_hidden_costs(prop: dict, listing_price: float | None = None) -> dict:
    surface    = prop.get("surface_m2") or 80
    year_built = prop.get("year_built")
    age        = (2026 - year_built) if year_built else None
    cert_raw   = prop.get("energy_cert")
    cert       = cert_raw.strip().upper() if cert_raw and cert_raw.strip() else None
    has_lift   = prop.get("has_lift", False)
    ite_status = prop.get("ite_status", "UNKNOWN")

    # IBI (municipal property tax) — BCN average rate ~0.75 % of cadastral value
    cadastral  = prop.get("cadastral_value") or (listing_price * 0.5 if listing_price else surface * 1_800)
    ibi_annual = round(cadastral * 0.0075)

    # Community fee: older buildings with lifts cost more to maintain
    age_known = age is not None
    community_monthly = (
        200 if has_lift and age_known and age > 40 else
        160 if has_lift else
        100 if age_known and age > 40 else
        80
    )

    # Derrama risk assessment
    if ite_status == "DESFAVORABLE":
        derrama_risk = "high"
    elif ite_status == "FAVORABLE":
        derrama_risk = "low" if (age is None or age < 50) else "medium"
    elif age is None:
        derrama_risk = "medium"
    elif age > 55:
        derrama_risk = "medium"
    elif age > 35:
        derrama_risk = "medium"
    else:
        derrama_risk = "low"

    derrama_provision = {"high": 150, "medium": 60, "low": 15}[derrama_risk]

    # Utility estimate
    utility_monthly = round(surface * 1.9)

    # Energy upgrade: only flag if cert is actually known to be E/F/G
    energy_upgrade_required = cert in ("E", "F", "G") if cert else False
    energy_upgrade_estimate = None
    if energy_upgrade_required and cert:
        base_cost = {"E": 9_000, "F": 16_000, "G": 28_000}[cert]
        energy_upgrade_estimate = round(base_cost * max(0.5, surface / 80))

    total_monthly = community_monthly + derrama_provision + utility_monthly
    total_annual  = round(ibi_annual + total_monthly * 12)

    return {
        "ibi_annual_eur":                ibi_annual,
        "community_fee_monthly_eur":     community_monthly,
        "utility_estimate_monthly_eur":  utility_monthly,
        "derrama_risk_label":            derrama_risk,
        "derrama_provision_monthly_eur": derrama_provision,
        "energy_upgrade_required":       energy_upgrade_required,
        "energy_upgrade_estimate_eur":   energy_upgrade_estimate,
        "total_monthly_eur":             total_monthly,
        "total_annual_eur":              total_annual,
    }


# Graduated energy future score — replaces the old binary 20/90 split.
# D→E is no longer a 70-pt cliff; each cert level has a meaningful difference.
_ENERGY_FUTURE: dict[str, int] = {
    "A": 100, "B": 90, "C": 78, "D": 62, "E": 35, "F": 15, "G": 5,
}


def score_hidden_costs(hidden_costs: dict, prop: dict | None = None) -> dict[str, float | None]:
    sub: dict[str, float | None] = {}

    # ── Derrama risk ──────────────────────────────────────────────────────────
    label = hidden_costs.get("derrama_risk_label")
    sub["derrama_risk"] = {"low": 90, "medium": 55, "high": 18}.get(label) if label else None

    # ── Energy future (EU 2033 efficiency mandate) ────────────────────────────
    cert = (prop.get("energy_cert") or "").strip().upper() if prop else ""
    sub["energy_future"] = _ENERGY_FUTURE.get(cert) if cert else None

    # ── Monthly holding cost vs BCN baseline ─────────────────────────────────
    monthly = hidden_costs.get("total_monthly_eur")
    if monthly is not None:
        # Baseline €400/mo for a typical 70 m² BCN flat (2025 avg: community
        # ~€120 + utilities ~€180 + IBI provision ~€65 + derrama buffer ~€35).
        # >€800/mo = 0 pts; reflects post-energy-crisis holding cost reality.
        sub["monthly_cost"] = max(0, min(100, round(100 - (monthly - 400) / 4)))
    else:
        sub["monthly_cost"] = None

    # ── IBI burden ───────────────────────────────────────────────────────────
    ibi = hidden_costs.get("ibi_annual_eur")
    if ibi is not None:
        # €500/yr → 100; €2500/yr → 0
        sub["ibi_burden"] = max(0, min(100, round(100 - (ibi - 500) / 20)))
    else:
        sub["ibi_burden"] = None

    return sub
