import hashlib
import json
import os
from datetime import datetime, timezone

_ANALYTICS_FILE = os.getenv("ANALYTICS_FILE", "/tmp/analytics.jsonl")
# No hardcoded default — require env var to be set for analytics access
_ANALYTICS_TOKEN = os.getenv("ANALYTICS_TOKEN", "")

_buffer: list[dict] = []


def _anon_ip(ip: str) -> str:
    """Anonymise IP: hash with a prefix to avoid storing raw PII."""
    if not ip or ip == "unknown":
        return "unknown"
    h = hashlib.sha256(ip.encode()).hexdigest()[:12]
    return f"ip:{h}"


def log_analysis(
    ip: str,
    address: str,
    score: int,
    disclosures_count: int,
    request_id: str,
    district: str = "",
    listing_price: float | None = None,
    buyer_profile: str = "balanced",
) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "ip_hash": _anon_ip(ip),
        "address": address,
        "district": district,
        "composite_score": score,
        "disclosures_count": disclosures_count,
        "listing_price": listing_price,
        "buyer_profile": buyer_profile,
    }
    _buffer.append(entry)
    print(f"[ANALYTICS] {json.dumps(entry)}", flush=True)
    try:
        with open(_ANALYTICS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def get_all() -> list[dict]:
    entries = {e["request_id"]: e for e in _buffer}
    try:
        with open(_ANALYTICS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                e = json.loads(line)
                entries[e.get("request_id", line[:8])] = e
    except Exception:
        pass
    return sorted(entries.values(), key=lambda e: e.get("ts", ""), reverse=True)


def get_summary() -> dict:
    all_entries = get_all()
    total = len(all_entries)
    unique_ips = len({e.get("ip") for e in all_entries})
    scores = [e["composite_score"] for e in all_entries if "composite_score" in e]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    districts: dict[str, int] = {}
    for e in all_entries:
        d = e.get("district", "")
        if d:
            districts[d] = districts.get(d, 0) + 1
    return {
        "total_analyses": total,
        "unique_ips": unique_ips,
        "avg_composite_score": avg_score,
        "top_districts": sorted(districts.items(), key=lambda x: -x[1])[:5],
    }
