"""User profile: questionnaire-driven weight computation.

Eight questions replace the old static buyer-profile labels.  Each answer
adjusts multipliers on the base dimension and sub-dimension weights; the
result is normalised so all weights still sum to 1.0 within their scope.

Legacy string profiles (balanced / family / investor / retiree / expat /
firsttime) are still accepted via compute_weights(legacy_profile=...) so the
/compare endpoint keeps working without changes.

Structural changes vs v1:
  - park_access removed from Convenience (merged into Intangible.green_urban_quality)
  - local_commerce removed from Intangible (OSM brand tags too unreliable)
  - price_vs_median + surface_efficiency removed from Property (pricing belongs in Market)
  - unit_features added to Property (terrace, parking, views, lift, floor)
  - days_on_market removed from Market sub-weights (informational only, not scored)
  - regulatory_risk removed from Risk sub-weights (effectively static; data missing)
  - Q8 lifestyle_priority added to control Intangible dimension weight
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class UserAnswers(BaseModel):
    # Q1 – Do you have children living with you?
    children_age: Optional[str] = None        # "none" | "young" (0-12) | "teen" (13-18)
    # Q2 – How long do you plan to stay / own this property?
    stay_duration: Optional[str] = None        # "short" (<5yr) | "medium" (5-15yr) | "long" (15yr+)
    # Q3 – Do you drive regularly / need on-street or garage parking?
    has_car: Optional[bool] = None
    # Q4 – Will you rent the property out?
    rental_intent: Optional[str] = None        # "none" | "long_term" | "short_term"
    # Q5 – How sensitive are you to nightlife noise?
    noise_tolerance: Optional[str] = None      # "love_it" | "neutral" | "need_quiet"
    # Q6 – Where do you primarily work?
    work_situation: Optional[str] = None       # "home" | "commute" | "retired"
    # Q7 – How comfortable are you with renovation / known defects?
    renovation_appetite: Optional[str] = None  # "ready" | "minor" | "move_in_ready"
    # Q8 – How important is access to cultural venues and local neighbourhood character?
    lifestyle_priority: Optional[str] = None   # "important" | "neutral" | "not_important"


# Legacy-profile → UserAnswers mapping (used by /compare)
_PROFILE_TO_ANSWERS: dict[str, UserAnswers] = {
    "balanced": UserAnswers(),
    "family": UserAnswers(
        children_age="young", stay_duration="long",
        noise_tolerance="need_quiet", renovation_appetite="move_in_ready",
    ),
    "investor": UserAnswers(
        rental_intent="long_term", stay_duration="short",
        lifestyle_priority="not_important",
    ),
    "retiree": UserAnswers(
        work_situation="retired", noise_tolerance="neutral",
        stay_duration="long", lifestyle_priority="important",
    ),
    "expat": UserAnswers(stay_duration="medium", renovation_appetite="minor"),
    "firsttime": UserAnswers(stay_duration="long", renovation_appetite="move_in_ready"),
}

# ── Base weights ─────────────────────────────────────────────────────────────

_BASE_DIM: dict[str, float] = {
    "Convenience": 0.13,
    "Safety":      0.13,
    "Property":    0.12,
    "Market":      0.12,
    "Risk":        0.13,
    "Liveability": 0.13,
    "HiddenCosts": 0.10,
    "Intangible":  0.14,
}

_BASE_SUB: dict[str, dict[str, float]] = {
    "Convenience": {
        # park_access removed — merged into Intangible.green_urban_quality
        "transit_proximity": 0.42,
        "amenity_density":   0.35,
        "google_quality":    0.23,
    },
    "Safety": {
        "theft_rate":    0.35,
        "vehicle_crime": 0.20,
        "night_safety":  0.30,
        "vandalism":     0.15,
    },
    "Property": {
        # price_vs_median + surface_efficiency removed — pricing belongs in Market
        # unit_features added: terrace, parking, views, lift, floor
        "building_era":  0.55,
        "orientation":   0.25,
        "unit_features": 0.20,
    },
    "Market": {
        # days_on_market removed from sub-weights; still computed and returned
        # as informational data but does not influence the composite score
        "price_trend":    0.30,
        "price_fairness": 0.45,
        "rental_yield":   0.25,
    },
    "Risk": {
        # regulatory_risk removed — BCN baseline was effectively static (72 for all);
        # heritage penalty folded into building_era context; STR risk captured by
        # tourist_saturation penalty in engine
        "flood_seismic":    0.22,
        "structural_risk":  0.30,
        "material_hazards": 0.30,
        "legal_clarity":    0.18,
    },
    "Liveability": {
        "school_quality": 0.30,
        "noise_day":      0.20,
        "noise_night":    0.28,
        "trajectory":     0.22,
    },
    "HiddenCosts": {
        "derrama_risk":  0.35,
        "monthly_cost":  0.30,
        "ibi_burden":    0.20,
        "energy_future": 0.15,
    },
    "Intangible": {
        # local_commerce removed — OSM brand tags too sparse and inconsistent
        # green_urban_quality boosted: now the sole park signal (park_access merged in)
        "cultural_density":    0.40,
        "local_market":        0.25,
        "green_urban_quality": 0.35,
    },
}


def compute_weights(
    answers: UserAnswers | None = None,
    legacy_profile: str | None = None,
) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """Return (dim_weights, sub_weights) personalised for the user's answers.

    Both output dicts are normalised: dim_weights sums to 1.0; each sub-dict
    sums to 1.0 within its dimension.
    """
    if answers is None and legacy_profile:
        answers = _PROFILE_TO_ANSWERS.get(legacy_profile)

    dim: dict[str, float] = {k: v for k, v in _BASE_DIM.items()}
    sub: dict[str, dict[str, float]] = {
        d: {k: v for k, v in ws.items()} for d, ws in _BASE_SUB.items()
    }

    if not answers:
        return _norm(dim), {d: _norm(ws) for d, ws in sub.items()}

    # ── Q1: Children ─────────────────────────────────────────────────────────
    if answers.children_age == "young":
        dim["Safety"]      *= 1.40
        dim["Liveability"] *= 1.50
        sub["Liveability"]["school_quality"] = 0.50
        sub["Liveability"]["noise_night"]    = 0.25
        sub["Liveability"]["noise_day"]      = 0.15
        sub["Liveability"]["trajectory"]     = 0.10
    elif answers.children_age == "teen":
        dim["Safety"]      *= 1.20
        dim["Liveability"] *= 1.20
        sub["Liveability"]["school_quality"] = 0.38
    elif answers.children_age == "none":
        sub["Liveability"]["school_quality"] = 0.08
        sub["Liveability"]["trajectory"]     = 0.48
        sub["Liveability"]["noise_night"]    = 0.28
        sub["Liveability"]["noise_day"]      = 0.16

    # ── Q2: Stay duration ────────────────────────────────────────────────────
    if answers.stay_duration == "short":
        dim["Market"] *= 1.60
        dim["Risk"]   *= 0.80
        sub["Market"]["price_trend"]    = 0.35
        sub["Market"]["price_fairness"] = 0.40
        sub["Market"]["rental_yield"]   = 0.25
    elif answers.stay_duration == "long":
        dim["Risk"]        *= 1.50
        dim["Liveability"] *= 1.25
        dim["Market"]      *= 0.75
        sub["Risk"]["structural_risk"]  = 0.32
        sub["Risk"]["material_hazards"] = 0.32

    # ── Q3: Car / parking ────────────────────────────────────────────────────
    if answers.has_car is True:
        sub["Convenience"]["transit_proximity"] = 0.12
        sub["Convenience"]["amenity_density"]   = 0.60
        sub["Convenience"]["google_quality"]    = 0.28
        sub["Safety"]["vehicle_crime"] = 0.32
        sub["Safety"]["theft_rate"]    = 0.28
        sub["Safety"]["night_safety"]  = 0.25
        sub["Safety"]["vandalism"]     = 0.15
    elif answers.has_car is False:
        sub["Convenience"]["transit_proximity"] = 0.60
        sub["Convenience"]["amenity_density"]   = 0.26
        sub["Convenience"]["google_quality"]    = 0.14
        sub["Safety"]["vehicle_crime"] = 0.08
        # boost remaining Safety weights proportionally via normalisation

    # ── Q4: Rental intent ────────────────────────────────────────────────────
    if answers.rental_intent == "long_term":
        dim["Market"] *= 1.35
        sub["Market"]["rental_yield"]   = 0.50
        sub["Market"]["price_fairness"] = 0.30
        sub["Market"]["price_trend"]    = 0.20
    elif answers.rental_intent == "short_term":
        dim["Market"] *= 1.50
        sub["Market"]["rental_yield"]   = 0.55
        sub["Market"]["price_fairness"] = 0.27
        sub["Market"]["price_trend"]    = 0.18

    # ── Q5: Noise tolerance ──────────────────────────────────────────────────
    if answers.noise_tolerance == "need_quiet":
        dim["Liveability"] *= 1.30
        sub["Liveability"]["noise_night"]    = 0.42
        sub["Liveability"]["noise_day"]      = 0.30
        sub["Liveability"]["trajectory"]     = 0.16
    elif answers.noise_tolerance == "love_it":
        sub["Liveability"]["noise_night"]    = 0.08
        sub["Liveability"]["noise_day"]      = 0.06
        sub["Liveability"]["trajectory"]     = 0.62
        sub["Liveability"]["school_quality"] = sub["Liveability"].get("school_quality", 0.30) * 0.75

    # ── Q6: Work situation ───────────────────────────────────────────────────
    if answers.work_situation == "home":
        dim["Liveability"] *= 1.20
        dim["Intangible"]  *= 1.25
        sub["Liveability"]["noise_day"] = max(
            0.28, sub["Liveability"].get("noise_day", 0.20) * 1.6
        )
    elif answers.work_situation == "commute":
        sub["Convenience"]["transit_proximity"] = max(
            0.55, sub["Convenience"].get("transit_proximity", 0.42)
        )
    elif answers.work_situation == "retired":
        dim["Convenience"] *= 1.25
        dim["Safety"]      *= 1.25
        dim["Liveability"] *= 1.20
        sub["Convenience"]["transit_proximity"] = max(
            0.40, sub["Convenience"].get("transit_proximity", 0.42)
        )

    # ── Q7: Renovation appetite ──────────────────────────────────────────────
    if answers.renovation_appetite == "move_in_ready":
        dim["HiddenCosts"] *= 1.50
        dim["Property"]    *= 1.20
        sub["Risk"]["structural_risk"]  = max(0.32, sub["Risk"].get("structural_risk", 0.30))
        sub["Risk"]["material_hazards"] = max(0.32, sub["Risk"].get("material_hazards", 0.30))
    elif answers.renovation_appetite == "ready":
        dim["HiddenCosts"] *= 0.70
        dim["Market"]      *= 1.15

    # ── Q8: Lifestyle / neighbourhood character ──────────────────────────────
    if answers.lifestyle_priority == "important":
        dim["Intangible"] *= 1.40
    elif answers.lifestyle_priority == "not_important":
        dim["Intangible"] *= 0.55

    return _norm(dim), {d: _norm(ws) for d, ws in sub.items()}


def _norm(d: dict) -> dict:
    total = sum(d.values())
    return {k: round(v / total, 4) for k, v in d.items()}
