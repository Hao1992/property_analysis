"""Risk dimension — four sub-dimensions covering physical, material, and legal risk.

Removed vs v1:
  regulatory_risk — BCN rent-control baseline was hardcoded 72 for virtually
    all properties (only pre-1940 heritage buildings scored 50). This made the
    sub-dimension nearly static and provided no useful signal for most buyers.
    Heritage renovation constraints are now surfaced in the AI narrative via
    building_era context. STR regulatory risk is captured by the
    tourist_saturation penalty in the engine.

Sub-dimensions:
  flood_seismic    — natural disaster zone (Spanish flood-zone classification)
  structural_risk  — building age + ITE inspection result
  material_hazards — era-specific material risks: aluminosis, asbestos, lead pipes
  legal_clarity    — title encumbrances / open charges on the property

Material hazard reference (Barcelona):
  Aluminosis (alumina cement): widely used 1960–1975, causes slow structural decay.
    Affects ~10 % of BCN apartment stock from this era.
  Asbestos: used until ~1975 (Uralita roofing, pipe lagging, floor tiles).
  Lead pipes: standard pre-1978; replaced gradually but many still in service.
"""
from __future__ import annotations


def score_risk(prop: dict, safety: dict, hidden_costs: dict | None = None) -> dict[str, float | None]:
    sub: dict[str, float | None] = {}

    # ── Flood / seismic zone ─────────────────────────────────────────────────
    flood_zone = prop.get("flood_zone")
    if flood_zone is not None:
        sub["flood_seismic"] = {"A": 18, "B": 48, "C": 82, "None": 100}.get(
            str(flood_zone), 82
        )
    else:
        sub["flood_seismic"] = None  # data not available — don't assume safe

    # ── Structural risk ───────────────────────────────────────────────────────
    year = prop.get("year_built")
    if year is not None:
        age = 2026 - year
        # Non-linear: older buildings degrade more steeply in the last 30 years
        struct_base = max(15, 100 - age * 0.55 - max(0, age - 50) * 0.3)
        ite = prop.get("ite_status", "UNKNOWN")
        ite_mod = 18 if ite == "FAVORABLE" else -22 if ite == "DESFAVORABLE" else 0
        sub["structural_risk"] = min(100, max(0, round(struct_base + ite_mod)))
    else:
        sub["structural_risk"] = None

    # ── Material hazards (era-specific) ─────────────────────────────────────
    sub["material_hazards"] = _material_hazards(year, prop.get("ite_status", "UNKNOWN"))

    # ── Legal clarity ────────────────────────────────────────────────────────
    open_charges = prop.get("open_charges")
    if open_charges is not None:
        sub["legal_clarity"] = max(0, 100 - open_charges * 20)
    else:
        sub["legal_clarity"] = None  # title search not performed yet

    return sub


def _material_hazards(year: int | None, ite_status: str) -> float | None:
    """Score material safety risk based on construction era.

    Returns None if year is unknown (can't assess era-specific hazards).
    """
    if year is None:
        return None

    base = 100

    # Aluminosis: high probability in 1960–1975 buildings
    if 1960 <= year < 1975:
        base -= 45
        # ITE FAVORABLE provides partial reassurance that the worst has not occurred
        if ite_status == "FAVORABLE":
            base += 18

    # Asbestos in construction materials: pre-1975 (Uralita, pipe lagging, tiles)
    if year < 1975:
        base -= 20
    elif year < 1980:
        base -= 8  # phase-out period

    # Lead pipes: standard pre-1978
    if year < 1978:
        base -= 15
    elif year < 1985:
        base -= 5  # partial replacement era

    # Heritage/poor-quality post-war materials
    if 1936 <= year < 1960:
        base -= 10  # scarcity-era construction quality

    return max(0, base)
