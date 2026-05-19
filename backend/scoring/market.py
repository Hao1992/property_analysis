"""Market dimension: price trend, price fairness, rental yield, market liquidity.

Key fixes:
  - rental_yield cap raised from 70 → 100 (previous cap artificially suppressed
    investor scores even for excellent-yield properties).
  - All sub-dims return None when the underlying data is missing, rather than
    using default values that would fabricate a signal.
  - days_on_market framed as 'market liquidity': low DOM = easier future exit,
    which is relevant to all buyers not just investors.
"""
from __future__ import annotations


def score_market(market_data: dict) -> dict[str, float | None]:
    sub: dict[str, float | None] = {}

    # ── Price trend (annual growth) ───────────────────────────────────────────
    growth = market_data.get("annual_growth_pct")
    if growth is not None:
        # 0 % → 50, +10 % → 100, -10 % → 0 (linear)
        sub["price_trend"] = min(100, max(0, round(50 + growth * 5)))
    else:
        sub["price_trend"] = None

    # ── Price fairness ────────────────────────────────────────────────────────
    # Prefer Fotocasa comparables position (real active listings, accurate).
    # Fall back to INE-based delta only when comparables are unavailable.
    comp_score = market_data.get("comparables_position_score")
    if comp_score is not None:
        sub["price_fairness"] = comp_score
    else:
        delta = market_data.get("vs_fair_value_pct")
        if delta is not None:
            sub["price_fairness"] = (
                100 if delta <= -5  else
                85  if delta <= 0   else
                70  if delta <= 5   else
                50  if delta <= 15  else
                20
            )
        else:
            sub["price_fairness"] = None

    # ── Rental yield vs city average ─────────────────────────────────────────
    yield_val  = market_data.get("rental_yield")
    city_yield = market_data.get("city_avg_yield")
    if yield_val is not None and city_yield and city_yield > 0:
        # city_avg → 65 pts; 1.5× avg → 97 pts; 2× avg → 100 pts
        sub["rental_yield"] = min(100, round((yield_val / city_yield) * 65))
    else:
        sub["rental_yield"] = None

    # ── Market liquidity (days on market) ─────────────────────────────────────
    # Low DOM = highly liquid market = easier exit strategy for buyers.
    # Note: for short-stay buyers this is positive; for negotiation leverage it's negative.
    # We score it as a market health / liquidity indicator.
    dom = market_data.get("days_on_market")
    if dom is not None:
        sub["days_on_market"] = (
            90 if dom < 30  else
            75 if dom < 60  else
            58 if dom < 90  else
            38
        )
    else:
        sub["days_on_market"] = None

    return sub
