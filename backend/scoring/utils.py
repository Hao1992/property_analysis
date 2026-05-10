from __future__ import annotations


def weighted_composite(
    items: list[tuple[str, float | None, float]],
) -> tuple[float | None, dict[str, float | None]]:
    """Weighted average that redistributes weight from None sub-dimensions.

    items: [(name, score_or_None, base_weight), ...]
    Returns (composite_or_None, sub_scores_dict).
    composite is None only when every sub-dimension has missing data.
    """
    sub: dict[str, float | None] = {n: s for n, s, _ in items}
    scored = [(n, s, w) for n, s, w in items if s is not None]
    if not scored:
        return None, sub
    total_w = sum(w for _, _, w in scored)
    composite = sum(s * w for _, s, w in scored) / total_w
    return round(composite), sub


def data_coverage(sub_scores: dict) -> float:
    """Fraction of sub-dimensions that have real data (not None), 0.0–1.0."""
    if not sub_scores:
        return 0.0
    return round(sum(1 for v in sub_scores.values() if v is not None) / len(sub_scores), 2)
