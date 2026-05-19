import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

_ANALYTICS_FILE = os.getenv("ANALYTICS_FILE", "/tmp/pa_analytics.jsonl")
_EVENTS_FILE    = os.getenv("EVENTS_FILE",    "/tmp/pa_events.jsonl")
_ANALYTICS_TOKEN = os.getenv("ANALYTICS_TOKEN", "")

_buffer: list[dict] = []
_events_buffer: list[dict] = []


def _anon_ip(ip: str) -> str:
    if not ip or ip == "unknown":
        return "unknown"
    return "ip:" + hashlib.sha256(ip.encode()).hexdigest()[:12]


def _price_bucket(price: Optional[float]) -> str:
    if price is None:
        return "unknown"
    if price < 200_000:   return "<200k"
    if price < 400_000:   return "200-400k"
    if price < 600_000:   return "400-600k"
    if price < 800_000:   return "600-800k"
    if price < 1_000_000: return "800k-1M"
    return ">1M"


def _write(path: str, entry: dict) -> None:
    try:
        with open(path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception:
        pass


def log_analysis(
    ip: str,
    address: str,
    score: float,
    disclosures_count: int,
    request_id: str,
    district: str = "",
    listing_price: Optional[float] = None,
    buyer_profile: str = "balanced",
    # extended fields
    language: str = "en",
    duration_ms: int = 0,
    fotocasa_success: bool = False,
    user_answers: Optional[dict] = None,
    score_dimensions: Optional[dict] = None,
    error: Optional[str] = None,
) -> None:
    entry = {
        "ts":               datetime.now(timezone.utc).isoformat(),
        "request_id":       request_id,
        "ip_hash":          _anon_ip(ip),
        "address":          address,
        "district":         district,
        "composite_score":  round(score) if score else None,
        "disclosures_count": disclosures_count,
        "price_bucket":     _price_bucket(listing_price),
        "has_price":        listing_price is not None,
        "buyer_profile":    buyer_profile,
        "language":         language,
        "duration_ms":      duration_ms,
        "fotocasa_success": fotocasa_success,
        "user_answers":     user_answers or {},
        "score_dimensions": score_dimensions or {},
        "error":            error,
    }
    _buffer.append(entry)
    _write(_ANALYTICS_FILE, entry)


def log_error(
    ip: str,
    address: str,
    error_type: str,
    error_msg: str,
    request_id: str = "",
) -> None:
    entry = {
        "ts":         datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "ip_hash":    _anon_ip(ip),
        "address":    address,
        "error_type": error_type,
        "error_msg":  str(error_msg)[:300],
    }
    _write(_ANALYTICS_FILE, {"__type": "error", **entry})


def log_track_event(
    session_id: str,
    request_id: str,
    event: str,
    data: dict,
) -> None:
    entry = {
        "ts":         datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "request_id": request_id,
        "event":      event,
        "data":       data,
    }
    _events_buffer.append(entry)
    _write(_EVENTS_FILE, entry)


def _read_file(path: str) -> list[dict]:
    entries = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return entries


def get_all() -> list[dict]:
    on_disk = {e["request_id"]: e for e in _read_file(_ANALYTICS_FILE) if "request_id" in e}
    from_buf = {e["request_id"]: e for e in _buffer if "request_id" in e}
    merged = {**on_disk, **from_buf}
    return sorted(merged.values(), key=lambda e: e.get("ts", ""), reverse=True)


def get_events() -> list[dict]:
    on_disk = _read_file(_EVENTS_FILE)
    return sorted(on_disk + _events_buffer, key=lambda e: e.get("ts", ""), reverse=True)


def get_summary() -> dict:
    entries = [e for e in get_all() if not e.get("__type")]
    total = len(entries)
    unique_ips = len({e.get("ip_hash") for e in entries})
    scores = [e["composite_score"] for e in entries if e.get("composite_score") is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    districts: dict[str, int] = {}
    for e in entries:
        d = e.get("district", "")
        if d:
            districts[d] = districts.get(d, 0) + 1
    return {
        "total_analyses": total,
        "unique_ips":      unique_ips,
        "avg_score":       avg_score,
        "top_districts":   sorted(districts.items(), key=lambda x: -x[1])[:5],
    }


def get_stats() -> dict:
    """Rich aggregations for the dashboard."""
    from collections import Counter, defaultdict
    from datetime import timedelta

    entries = [e for e in get_all() if not e.get("__type")]
    events  = get_events()

    now = datetime.now(timezone.utc)

    # — daily counts (last 14 days) —
    day_counts: dict[str, int] = {}
    for i in range(14):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        day_counts[day] = 0
    for e in entries:
        day = e.get("ts", "")[:10]
        if day in day_counts:
            day_counts[day] += 1
    daily = [{"date": d, "count": c} for d, c in sorted(day_counts.items())]

    today  = now.strftime("%Y-%m-%d")
    week_start = (now - timedelta(days=6)).strftime("%Y-%m-%d")
    today_count = sum(1 for e in entries if e.get("ts", "")[:10] == today)
    week_count  = sum(1 for e in entries if e.get("ts", "")[:10] >= week_start)

    # — language split —
    lang_counts = Counter(e.get("language", "en") for e in entries)

    # — price buckets —
    price_counts = Counter(e.get("price_bucket", "unknown") for e in entries)
    bucket_order = ["<200k", "200-400k", "400-600k", "600-800k", "800k-1M", ">1M", "unknown"]
    price_dist = [{"bucket": b, "count": price_counts.get(b, 0)} for b in bucket_order]

    # — district distribution —
    district_counts = Counter(e.get("district", "") for e in entries if e.get("district"))
    top_districts = [{"district": d, "count": c} for d, c in district_counts.most_common(10)]

    # — fotocasa success rate —
    fc_total   = sum(1 for e in entries if "fotocasa_success" in e)
    fc_success = sum(1 for e in entries if e.get("fotocasa_success") is True)
    fc_rate = round(fc_success / fc_total * 100) if fc_total else None

    # — duration percentiles —
    durations = sorted(e["duration_ms"] for e in entries if e.get("duration_ms", 0) > 0)
    def pct(lst, p):
        if not lst: return None
        idx = int(len(lst) * p / 100)
        return lst[min(idx, len(lst) - 1)]
    dur_p50 = pct(durations, 50)
    dur_p95 = pct(durations, 95)

    # — score distribution (buckets of 10) —
    score_buckets: dict[str, int] = {f"{i*10}-{i*10+9}": 0 for i in range(10)}
    for e in entries:
        s = e.get("composite_score")
        if s is not None:
            bucket = f"{(s // 10) * 10}-{(s // 10) * 10 + 9}"
            if bucket in score_buckets:
                score_buckets[bucket] += 1
    score_dist = [{"range": r, "count": c} for r, c in score_buckets.items()]

    # — buyer profile distribution —
    profile_counts = Counter(e.get("buyer_profile", "balanced") for e in entries)

    # — frontend events summary —
    section_views = Counter()
    pdf_count = 0
    lang_switch_count = 0
    for ev in events:
        if ev.get("event") == "section_view":
            section_views[ev.get("data", {}).get("section", "?")] += 1
        elif ev.get("event") == "pdf_download":
            pdf_count += 1
        elif ev.get("event") == "language_switch":
            lang_switch_count += 1
    top_sections = [{"section": s, "views": c} for s, c in section_views.most_common(10)]

    # — recent 20 entries —
    recent = []
    for e in entries[:20]:
        recent.append({
            "ts":        e.get("ts", "")[:16].replace("T", " "),
            "address":   e.get("address", "")[:45],
            "district":  e.get("district", ""),
            "score":     e.get("composite_score"),
            "price":     e.get("price_bucket", ""),
            "lang":      e.get("language", "en"),
            "dur_s":     round(e["duration_ms"] / 1000, 1) if e.get("duration_ms") else "—",
            "fotocasa":  "✓" if e.get("fotocasa_success") else "✗",
        })

    return {
        "total":          len(entries),
        "today":          today_count,
        "week":           week_count,
        "unique_ips":     len({e.get("ip_hash") for e in entries}),
        "avg_score":      round(sum(e["composite_score"] for e in entries if e.get("composite_score") is not None) / max(len(entries), 1), 1),
        "daily":          daily,
        "languages":      dict(lang_counts),
        "price_dist":     price_dist,
        "districts":      top_districts,
        "fc_rate":        fc_rate,
        "fc_total":       fc_total,
        "dur_p50":        dur_p50,
        "dur_p95":        dur_p95,
        "score_dist":     score_dist,
        "profiles":       dict(profile_counts),
        "top_sections":   top_sections,
        "pdf_downloads":  pdf_count,
        "lang_switches":  lang_switch_count,
        "recent":         recent,
    }
