"""
Fotocasa market comparables scraper.

Fetches active comparable listings for a district+size range.
Falls back to a calibrated static table when cookies are missing/expired.

Cookie strategy: The FOTOCASA_COOKIES env var holds the reese84 session cookie
string (copied from a real browser session). Expires every ~2 weeks.
Refresh by visiting fotocasa.es, running:
  document.cookie  (in browser console)
and pasting the result into Railway env vars.
"""
import os
import re
import logging
import statistics
import asyncio
from typing import Optional

import httpx

log = logging.getLogger(__name__)

# Fotocasa URL slugs for each BCN district
DISTRICT_SLUGS: dict[str, str] = {
    "Eixample":              "eixample",
    "Sarrià-Sant Gervasi":   "sarria-sant-gervasi",
    "Les Corts":             "les-corts",
    "Gràcia":                "gracia",
    "Nou Barris":            "nou-barris",
    "Sant Andreu":           "sant-andreu",
    "Sant Martí":            "sant-marti",
    "Sants-Montjuïc":        "sants-montjuic",
    "Horta-Guinardó":        "horta-guinardo",
    "Ciutat Vella":          "ciutat-vella",
}

# Calibrated district price ranges (€/m², 2024-2025, all conditions + sizes)
# Source: Fotocasa medians confirmed via scraping + Tinsa Q4 2024 reports
# p25 = lower quartile, median = median, p75 = upper quartile
DISTRICT_STATIC: dict[str, dict] = {
    "Eixample":              {"p25": 4400, "median": 6000, "p75": 9500},
    "Sarrià-Sant Gervasi":   {"p25": 5200, "median": 7800, "p75": 12500},
    "Les Corts":             {"p25": 4600, "median": 6600, "p75": 9200},
    "Gràcia":                {"p25": 4300, "median": 6000, "p75": 8800},
    "Ciutat Vella":          {"p25": 4100, "median": 6000, "p75": 9200},
    "Sant Martí":            {"p25": 3600, "median": 5300, "p75": 7600},
    "Sants-Montjuïc":        {"p25": 3100, "median": 4600, "p75": 6600},
    "Horta-Guinardó":        {"p25": 2600, "median": 3900, "p75": 5600},
    "Nou Barris":            {"p25": 2100, "median": 3300, "p75": 4600},
    "Sant Andreu":           {"p25": 2600, "median": 3900, "p75": 5200},
}
_DEFAULT_RANGE = {"p25": 3500, "median": 5000, "p75": 7500}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
}


def _parse_listings(html: str) -> list[dict]:
    """
    Extract price+surface pairs from Fotocasa HTML.
    Data is in a large JSON-like script tag with the pattern:
      "price":"XXX.XXX €" ... "key":"surface","value":N
    """
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    # Find the big embedded data script (usually >100KB)
    big = next((s for s in scripts if len(s) > 50000 and '"price"' in s), None)
    if not big:
        return []

    matches = re.findall(
        r'"price"\s*:\s*"([\d\.]+)\s*€"'
        r'.*?"key"\s*:\s*"surface"\s*,\s*"value"\s*:\s*(\d+)',
        big, re.DOTALL
    )

    listings = []
    for price_str, surface_str in matches:
        try:
            price = int(price_str.replace(".", ""))
            size = int(surface_str)
            if 20 < size < 500 and 50_000 < price < 20_000_000:
                listings.append({"price": price, "size": size, "ppm2": round(price / size)})
        except (ValueError, ZeroDivisionError):
            continue
    return listings


async def get_market_comparables(
    district: str,
    surface_m2: Optional[float],
    listing_price: Optional[float] = None,
) -> dict:
    """
    Returns market context for a property: median, P25, P75, comparable listings.
    Tries Fotocasa live data first; falls back to calibrated static table.
    """
    size = surface_m2 or 90.0
    min_size = max(20, round(size * 0.70 / 10) * 10)
    max_size = round(size * 1.40 / 10) * 10
    size_range = f"{min_size}–{max_size} m²"

    slug = DISTRICT_SLUGS.get(district)
    static = DISTRICT_STATIC.get(district, _DEFAULT_RANGE)
    cookies = os.getenv("FOTOCASA_COOKIES", "")

    listings: list[dict] = []

    if slug and cookies:
        url = (
            f"https://www.fotocasa.es/es/comprar/viviendas/barcelona/{slug}/l"
            f"?minSize={min_size}&maxSize={max_size}"
        )
        try:
            async with httpx.AsyncClient(
                headers={**_HEADERS, "Cookie": cookies},
                follow_redirects=True,
                timeout=15,
            ) as client:
                r = await client.get(url)
            if r.status_code == 200 and len(r.text) > 100_000:
                raw = _parse_listings(r.text)
                # Filter to target size range
                listings = [
                    l for l in raw
                    if min_size * 0.8 <= l["size"] <= max_size * 1.2
                    and 2000 < l["ppm2"] < 30000
                ]
                log.info(
                    "Fotocasa scrape OK: %d listings for %s %s",
                    len(listings), district, size_range
                )
        except Exception as exc:
            log.warning("Fotocasa scrape failed (%s) — using static table", exc)

    # Compute stats
    if len(listings) >= 5:
        ppm2s = [l["ppm2"] for l in listings]
        median_ppm2 = int(statistics.median(ppm2s))
        p25 = int(statistics.quantiles(ppm2s, n=4)[0])
        p75 = int(statistics.quantiles(ppm2s, n=4)[2])
        source = "Fotocasa"
        count = len(listings)
        # Return up to 6 representative listings spread across the range
        listings_sorted = sorted(listings, key=lambda x: x["ppm2"])
        sample_indices = _spread_sample(len(listings_sorted), 6)
        sample = [listings_sorted[i] for i in sample_indices]
    else:
        # Static fallback
        median_ppm2 = static["median"]
        p25 = static["p25"]
        p75 = static["p75"]
        source = "district statistics"
        count = None
        sample = []

    # Compute asking position in range
    asking_ppm2 = round(listing_price / size) if listing_price and size else None
    position = _range_position(asking_ppm2, p25, p75) if asking_ppm2 else None

    return {
        "median_ppm2":   median_ppm2,
        "p25_ppm2":      p25,
        "p75_ppm2":      p75,
        "listings":      sample,
        "count":         count,
        "source":        source,
        "district":      district,
        "size_range":    size_range,
        "asking_ppm2":   asking_ppm2,
        "position":      position,
    }


def _spread_sample(total: int, n: int) -> list[int]:
    """Return n evenly spread indices across a list of `total` items."""
    if total <= n:
        return list(range(total))
    step = (total - 1) / (n - 1)
    return [round(i * step) for i in range(n)]


def _range_position(asking_ppm2: int, p25: int, p75: int) -> str:
    """Classify asking price position relative to district range."""
    if asking_ppm2 < p25 * 0.85:
        return "well_below"
    if asking_ppm2 < p25:
        return "below"
    if asking_ppm2 <= p75:
        return "within_range"
    if asking_ppm2 <= p75 * 1.3:
        return "above"
    return "well_above"
