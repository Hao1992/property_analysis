"""Liveability dimension: school quality, noise (day/night), neighbourhood trajectory.

School quality is scored on QUALITY of nearby schools (Google rating + type),
not quantity — the number of schools within 500 m is largely irrelevant; what
matters is whether the nearest ones are good.

Neighbourhood trajectory stays here (not in Risk) because it primarily affects
day-to-day quality of life rather than financial/structural risk.
"""
from __future__ import annotations


def score_liveability(
    school: dict,
    noise: dict,
    trajectory: dict,
) -> dict[str, float | None]:
    sub: dict[str, float | None] = {}

    # ── School quality ────────────────────────────────────────────────────────
    raw = school.get("composite_score")
    sub["school_quality"] = float(raw) if raw is not None else None

    # ── Day noise ─────────────────────────────────────────────────────────────
    day = noise.get("day_noise_score")
    sub["noise_day"] = float(day) if day is not None else None

    # ── Night noise (weighted higher — sleep quality) ─────────────────────────
    night = noise.get("night_noise_score")
    sub["noise_night"] = float(night) if night is not None else None

    # ── Neighbourhood trajectory ───────────────────────────────────────────────
    traj = trajectory.get("trend_score")
    sub["trajectory"] = float(traj) if traj is not None else None

    return sub
