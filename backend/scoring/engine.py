"""Composite scoring engine — v3.

Architecture changes from v2:
  - bad_energy penalty REMOVED: energy_future sub-dim in HiddenCosts already
    captures this with a graduated scale (A=100 → G=5). Double-penalising
    the same cert letter inflated its impact beyond all other factors.
  - tourist_saturation penalty now respects rental_intent: short-term rental
    buyers see a small bonus in high-demand zones (demand = revenue); only
    quality-of-life / long-term buyers receive the saturation penalty.
  - _dim() fallback weight changed from 0.10 → 0.0: sub-dimensions not
    present in sub_weights are skipped from composite calculation. This makes
    days_on_market "informational only" (still in sub_scores for display, but
    removed from _BASE_SUB so it doesn't influence the score).
  - penalty_breakdown added to return dict: shows which penalties fired and
    their approximate points impact, giving users a clear explanation.
"""
from __future__ import annotations

from models.user_profile import UserAnswers, compute_weights
from scoring.utils import weighted_composite, data_coverage
from scoring.convenience import score_convenience
from scoring.safety import score_safety
from scoring.property_score import score_property
from scoring.market import score_market
from scoring.risk import score_risk
from scoring.liveability import score_liveability
from scoring.hidden_costs import score_hidden_costs
from scoring.intangible import score_intangible


def calculate_composite(
    poi_dict: dict,
    enriched_poi: dict,
    safety_data: dict,
    prop_data: dict,
    valuation_data: dict,
    market_data: dict,
    school_data: dict,
    noise_data: dict,
    trajectory_data: dict,
    hidden_costs_data: dict,
    airbnb_data: dict,
    user_answers: UserAnswers | None = None,
    legacy_profile: str | None = None,
) -> dict:
    dim_w, sub_w = compute_weights(user_answers, legacy_profile)

    # ── Collect sub-scores from each dimension ────────────────────────────────
    conv_sub = score_convenience(poi_dict, enriched_poi)
    safe_sub = score_safety(safety_data)
    prop_sub = score_property(prop_data, valuation_data)
    mkt_sub  = score_market(market_data)
    risk_sub = score_risk(prop_data, safety_data, hidden_costs_data)
    live_sub = score_liveability(school_data, noise_data, trajectory_data)
    cost_sub = score_hidden_costs(hidden_costs_data, prop_data)
    intg_sub = score_intangible(poi_dict, enriched_poi)

    # ── Compute dimension composites ──────────────────────────────────────────
    # Keys not in sub_weights (e.g. days_on_market) get 0.0 weight — they
    # appear in sub_scores for display but do not affect the composite.
    def _dim(sub_scores: dict, dim_name: str) -> float | None:
        weights = sub_w[dim_name]
        items = [(k, sub_scores.get(k), weights.get(k, 0.0)) for k in sub_scores]
        # Exclude zero-weight items from the composite (informational only)
        items = [(k, s, w) for k, s, w in items if w > 0]
        score, _ = weighted_composite(items)
        return score

    conv_score = _dim(conv_sub, "Convenience")
    safe_score = _dim(safe_sub, "Safety")
    prop_score = _dim(prop_sub, "Property")
    mkt_score  = _dim(mkt_sub,  "Market")
    risk_score = _dim(risk_sub, "Risk")
    live_score = _dim(live_sub, "Liveability")
    cost_score = _dim(cost_sub, "HiddenCosts")
    intg_score = _dim(intg_sub, "Intangible")

    # ── Pre-penalty composite (None dimensions are redistributed) ─────────────
    dim_items = [
        ("Convenience", conv_score, dim_w["Convenience"]),
        ("Safety",      safe_score, dim_w["Safety"]),
        ("Property",    prop_score, dim_w["Property"]),
        ("Market",      mkt_score,  dim_w["Market"]),
        ("Risk",        risk_score, dim_w["Risk"]),
        ("Liveability", live_score, dim_w["Liveability"]),
        ("HiddenCosts", cost_score, dim_w["HiddenCosts"]),
        ("Intangible",  intg_score, dim_w["Intangible"]),
    ]
    pre_penalty_raw, _ = weighted_composite(dim_items)
    pre_penalty = pre_penalty_raw if pre_penalty_raw is not None else 50

    # ── Penalty multipliers ───────────────────────────────────────────────────
    penalties: dict[str, float] = {}

    # Critical structural / material risk: any sub-score below 20
    penalties["critical_risk"] = 0.70 if any(
        v is not None and v < 20 for v in risk_sub.values()
    ) else 1.0

    # Overpricing vs estimated fair value.
    # When valuation confidence is low (< 0.7), INE median data is stale or
    # unavailable for this census section — do not punish with a hard penalty.
    # Instead, scale the penalty toward 1.0 proportionally to unreliability.
    delta = valuation_data.get("vs_listing_pct") or 0
    val_conf = valuation_data.get("confidence", 1.0)
    raw_penalty = (
        0.80 if delta > 25 else
        0.88 if delta > 15 else
        0.94 if delta > 8  else
        1.0
    )
    if val_conf < 0.7 and raw_penalty < 1.0:
        # Blend toward 1.0 (no penalty) based on how unreliable the data is
        blend = val_conf / 0.7          # 0.0 when conf=0, 1.0 when conf=0.7
        penalties["overpriced"] = 1.0 - (1.0 - raw_penalty) * blend
    else:
        penalties["overpriced"] = raw_penalty

    # High derrama risk (surprise major repair assessment)
    penalties["derrama_risk"] = 0.93 if hidden_costs_data.get("derrama_risk_label") == "high" else 1.0

    # Tourist saturation — direction depends on the buyer's rental intent:
    #   short-term rental investors: high Airbnb demand is a positive signal
    #   long-term rental / owner-occupier / unknown: saturation hurts QoL
    rental_intent = (user_answers.rental_intent if user_answers else None)
    if airbnb_data.get("risk_label") == "very_high":
        if rental_intent == "short_term":
            penalties["tourist_saturation"] = 1.04   # demand premium for STR
        elif rental_intent == "long_term":
            penalties["tourist_saturation"] = 0.97   # mild QoL friction for tenants
        else:
            penalties["tourist_saturation"] = 0.94   # saturation hurts resident QoL
    else:
        penalties["tourist_saturation"] = 1.0

    mult = 1.0
    for v in penalties.values():
        mult *= v
    composite = round(pre_penalty * mult)

    # ── Penalty breakdown — approximate points impact per penalty ─────────────
    # Shows each active penalty individually against pre_penalty so users
    # understand exactly what is dragging their score down (or up).
    penalty_breakdown = []
    for name, p_mult in penalties.items():
        if p_mult == 1.0:
            continue
        approx_pts = round(pre_penalty * (p_mult - 1.0))
        penalty_breakdown.append({
            "name":         name,
            "multiplier":   p_mult,
            "approx_points": approx_pts,   # negative = penalty, positive = bonus
        })

    # ── Overall confidence (fraction of all sub-dims with real data) ───────────
    all_sub = {
        **{f"conv_{k}": v for k, v in conv_sub.items()},
        **{f"safe_{k}": v for k, v in safe_sub.items()},
        **{f"prop_{k}": v for k, v in prop_sub.items()},
        **{f"mkt_{k}":  v for k, v in mkt_sub.items()},
        **{f"risk_{k}": v for k, v in risk_sub.items()},
        **{f"live_{k}": v for k, v in live_sub.items()},
        **{f"cost_{k}": v for k, v in cost_sub.items()},
        **{f"intg_{k}": v for k, v in intg_sub.items()},
    }
    confidence = data_coverage(all_sub)

    grade = (
        "Excellent buy"          if composite >= 85 else
        "Good buy"               if composite >= 70 else
        "Proceed with caution"   if composite >= 55 else
        "High risk — reconsider"
    )

    return {
        "composite":             composite,
        "composite_pre_penalty": round(pre_penalty),
        "grade":                 grade,
        "confidence":            confidence,
        "penalty_multipliers":   penalties,
        "penalty_breakdown":     penalty_breakdown,
        "dimensions": [
            _dim_dict("Convenience", conv_score, dim_w["Convenience"], conv_sub, sub_w["Convenience"]),
            _dim_dict("Safety",      safe_score, dim_w["Safety"],      safe_sub, sub_w["Safety"]),
            _dim_dict("Property",    prop_score, dim_w["Property"],    prop_sub, sub_w["Property"]),
            _dim_dict("Market",      mkt_score,  dim_w["Market"],      mkt_sub,  sub_w["Market"]),
            _dim_dict("Risk",        risk_score, dim_w["Risk"],        risk_sub, sub_w["Risk"]),
            _dim_dict("Liveability", live_score, dim_w["Liveability"], live_sub, sub_w["Liveability"]),
            _dim_dict("HiddenCosts", cost_score, dim_w["HiddenCosts"], cost_sub, sub_w["HiddenCosts"]),
            _dim_dict("Intangible",  intg_score, dim_w["Intangible"],  intg_sub, sub_w["Intangible"]),
        ],
    }


def _dim_dict(
    name: str,
    score: float | None,
    weight: float,
    sub_scores: dict[str, float | None],
    sub_weights: dict[str, float],
) -> dict:
    return {
        "name":        name,
        "score":       score,
        "weight":      weight,
        "sub_scores":  sub_scores,
        "sub_weights": sub_weights,
        "coverage":    data_coverage(sub_scores),
    }
