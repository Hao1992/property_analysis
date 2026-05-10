"""Property dimension: physical quality of the building and specific unit.

Three sub-dimensions replace the previous four:
  building_era   — construction era determines material quality, hazard risk,
                   and renovation constraints (most important)
  orientation    — solar exposure (Catastro code); affects comfort and energy
  unit_features  — specific unit attributes: terrace, parking, views, lift,
                   floor level, renovation status

Removed vs v1:
  price_vs_median   → moved to Market (pricing signals belong together)
  surface_efficiency → effectively duplicated price_vs_median; removed

ERA risk profiles (Barcelona-specific):
  pre-1936   Solid masonry, lead pipes, possible heritage listing.
  1936–1960  Post-war austerity; poor-quality materials due to scarcity.
  1960–1975  Desarrollismo boom: HIGHEST RISK — aluminosis, asbestos, lead pipes.
  1975–1995  Transition; improving but highly variable, many ITE renewals due.
  1995–2007  Pre-CTE building code; modern but energy-inefficient.
  2007+      CTE-compliant modern construction.
"""
from __future__ import annotations

# Era base scores reflect material quality, known hazards, and structural integrity.
# ITE status is applied as a modifier on top.
_ERA_SCORE: list[tuple[int, int, int]] = [
    # (year_from_inclusive, year_to_exclusive, base_score)
    (0,    1936, 65),   # pre-1936: solid but aged; lead pipes deduct in Risk
    (1936, 1960, 40),   # post-war austerity: genuinely poor materials
    (1960, 1975, 28),   # desarrollismo: highest risk era (aluminosis etc.)
    (1975, 1995, 55),   # transition: better but variable
    (1995, 2007, 72),   # pre-CTE: modern build quality, poor energy
    (2007, 9999, 88),   # CTE-compliant: current standards
]

# Spanish catastro orientation codes (note: West = "O" in Spanish)
_ORIENTATION_SCORE: dict[str, int] = {
    "S":  95,   # South: warm winter sun, manageable summer with blinds
    "SE": 88,
    "SO": 80,
    "E":  72,   # East: morning light, cool afternoons — good in BCN heat
    "NE": 52,
    "O":  48,   # West: afternoon western sun — hot in BCN summers
    "NO": 38,
    "N":  26,   # North: poor light, cold in winter
}


def score_property(prop: dict, valuation: dict) -> dict[str, float | None]:
    sub: dict[str, float | None] = {}

    # ── Building era ─────────────────────────────────────────────────────────
    year = prop.get("year_built")
    if year is not None:
        base = next(
            (s for (lo, hi, s) in _ERA_SCORE if lo <= year < hi),
            55,
        )
        ite = prop.get("ite_status", "UNKNOWN")
        ite_adj = 15 if ite == "FAVORABLE" else -25 if ite == "DESFAVORABLE" else 0
        sub["building_era"] = min(100, max(0, base + ite_adj))
    else:
        sub["building_era"] = None

    # ── Solar orientation ─────────────────────────────────────────────────────
    orientation = (prop.get("orientation") or "").strip().upper()
    sub["orientation"] = _ORIENTATION_SCORE.get(orientation) if orientation else None

    # ── Unit features ─────────────────────────────────────────────────────────
    sub["unit_features"] = _unit_features(prop)

    return sub


def _unit_features(prop: dict) -> float | None:
    """Score unit-level physical features independent of the building.

    Returns None when no feature data is present in the listing (don't
    fabricate a neutral 50 — absence of data is not the same as average).
    Starting baseline 42 for a bare unit; features push it up to 100.
    """
    feature_keys = ["has_lift", "has_terrace", "has_parking", "has_views", "renovated", "floor"]
    if not any(k in prop for k in feature_keys):
        return None

    score = 42  # baseline: basic unit, no notable features
    if prop.get("has_lift"):    score += 8
    if prop.get("has_terrace"): score += 12
    if prop.get("has_parking"): score += 16
    if prop.get("has_views"):   score += 18
    if prop.get("renovated"):   score += 10
    floor = prop.get("floor") or 0
    if floor >= 5:   score += 5
    elif floor >= 3: score += 2

    return min(100, score)


def era_label(year_built: int | None) -> str:
    """Human-readable era label for AI narrative."""
    if year_built is None:
        return "unknown era"
    for lo, hi, _ in _ERA_SCORE:
        if lo <= year_built < hi:
            labels = {
                0:    "pre-Civil War masonry (pre-1936)",
                1936: "post-war austerity construction (1936–1960)",
                1960: "development boom — aluminosis risk era (1960–1975)",
                1975: "transition period (1975–1995)",
                1995: "pre-CTE modern (1995–2007)",
                2007: "CTE-compliant modern (2007+)",
            }
            return labels.get(lo, "")
    return "unknown era"
