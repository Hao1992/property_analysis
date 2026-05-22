## Development Process

### Review Protocol (mandatory for any feature touching production)

This project had a major quality incident during initial feature development — 10 "completed" features had 18 bugs including 3 that caused HTTP 500 crashes on every request. The following protocol is now required.

#### The 3-round rule

Any non-trivial change (new endpoint, new component, data model change) requires:

**Round 1 — Code review before running anything**
- Does every new dict iteration guard against non-list values?
- Are all Pydantic model types consistent with what services actually return? (Optional[int] vs int)
- Do all frontend fetch() URLs match Vite proxy config AND backend route paths?
- Are all numeric calculations correct? (Don't trust fast mental math — verify with actual numbers)

**Round 2 — Live API testing with real numbers**
- Start the backend and curl every new endpoint
- Verify output values make domain sense (€185k cash needed, not €500k)
- Test edge cases: what happens when the CSV is missing? When Overpass is down?

**Round 3 — Independent review (different perspective)**
- Someone who didn't write the code reads it and checks Round 1 items again
- At minimum, do a final TypeScript + Python syntax check

#### Specific checks that caught real bugs in this project

1. **Dict iteration with mixed types**: When adding metadata keys (int, bool) to a dict that is also iterated, add `isinstance(pois, list)` guard at EVERY loop site — not just one. This project had the bug in 4 places.

2. **Pydantic Optional types**: When a service function starts returning `None` for a field, the response model must be updated to `Optional[X]`. A mismatch causes silent crashes when that code path is hit.

3. **Frontend URL → Vite proxy → FastAPI route must all match**: New endpoints need entries in ALL three: `vite.config.ts` proxy, the component's `fetch()` call, and the FastAPI `@router.post()`. Missing any one → 404 in dev.

4. **Financial calculations — verify with real numbers**: `minimum_cash_required = price + total` was wrong when a mortgage was provided. The correct formula is `(price - mortgage) + total`. Always run the formula with a concrete example: €450k price, €315k mortgage → should need €185k cash, not €500k.

5. **Tax law accuracy**: Never trust fast estimates for tax rates. Verify against official sources:
   - Catalonia ITP: flat 10% up to €600k, then progressive 11%/12%/13% (DL5/2025 per atc.gencat.cat)
   - Madrid AJD: 0.75% (not 0.7%)
   - IRNR: multiply imputed income BASE (1.1%) by the TAX RATE (19%) — the actual tax is ~0.2% of cadastral, not 1.1%

6. **Third-party API sanity checks**: OSRM public demo server returns driving-speed data for foot routing. Any external API response that implies a human walking at 60 km/h needs a sanity cap before showing to users.

#### What "done" means

A feature is done when:
- [ ] Python syntax check passes (`py_compile` on all modified files)
- [ ] TypeScript check passes (`npx tsc --noEmit`)
- [ ] Backend starts without errors
- [ ] New endpoints respond correctly to curl with realistic inputs
- [ ] Output values make domain sense (verified with hand calculation)
- [ ] Edge cases tested (what if external API fails? what if optional field is None?)

"TypeScript compiles" is not "done". "Tests pass" is not "done" if there are no tests for the new code path.

### Data quality standards

Before showing any number to a user, answer:
1. **Source**: Where does this number come from? Is the source reliable?
2. **Confidence**: Is this a verified official figure or an estimate? Label it accordingly with `ConfidenceBadge`.
3. **Failure mode**: What does the UI show when the data source fails? Never show a fake/hardcoded number as if it were real (the Airbnb district fallback bug showed 95 listings as if they were counted for that specific address).
4. **Domain check**: Does this number make sense for the domain? (€500k cash needed to buy a €450k apartment is impossible — any system producing this number is broken.)

### Confidence labeling

All data cards must display a `ConfidenceBadge`:
- `verified` (green ✓): Official government data, verified source, address-specific
- `estimated` (amber ~): Model-derived, directionally correct, source may have gaps
- `district` (amber ~): Official data but district-level only, not address-specific

When data source fails, show the failure honestly — never substitute fake numbers silently.

---

## Current Feature State (as of 2026-05-21)

### Parking — Area Verda integration (`backend/services/parking.py`)
- **Data source**: Official Barcelona Area Verda JSON (`areaverda.cat/sites/default/files/GetMappingObjects.json`)
- **What it does**: Downloads and caches the full regulated street-parking map, finds nearest segments to the property, determines resident zone (A/B/C/D), and computes monthly resident permit cost vs. public garage alternatives
- **Caching**: Local file cache with daily TTL (`AREA_VERDA_CACHE_TTL_SECONDS`). Falls back gracefully if download fails.
- **Confidence**: `verified` for zone type (official data), `estimated` for garage pricing
- **⚠ Parking prices are always marked `unverified`** — do not change this; garage prices are scraped/estimated and not authoritative
- **Env var**: `AREA_VERDA_JSON_URL` (default points to official source)

### Analytics — Postgres persistence (`backend/utils/analytics.py`)
- **What it does**: Persists every analysis event (address, score, user type, duration) to a Postgres database for the admin dashboard
- **Env var**: `DATABASE_URL` (optional). When unset → falls back to ephemeral local files under `/tmp`
- **Recommended**: Neon / Supabase / Aiven free tier in production
- **Dashboard token**: `ANALYTICS_TOKEN` env var gates access to `/dashboard` route
- **Dependency**: `psycopg` (not psycopg2) — listed in `requirements.txt`

### Disclosures service (`backend/services/disclosures.py`)
- Returns legal disclosure flags (touristic license moratorium, protected buildings, flood zones, etc.)
- Fixed: `handle missing disclosure values` — all fields now `Optional` with safe fallbacks; no more 500s when a field is absent

### Rate limiter update (`backend/utils/rate_limiter.py`)
- Added `RATE_LIMIT_WHITELIST` env var support for IP-based bypass (useful for internal health checks)
- Quota refund on failed analysis: if the analysis pipeline throws, the quota slot is returned to the user

### Request timeout guard (`backend/api/routes/analyze.py`)
- Entire analysis pipeline wrapped in `asyncio.timeout(25)` — if any combination of external calls exceeds 25s, the request returns partial results instead of letting Railway's proxy kill it without CORS headers (which browsers report as "Network Error")

---

## Infrastructure & Deployment

| Component | Host | Notes |
|-----------|------|-------|
| Frontend | Vercel (`hsproperty-analysis.vercel.app`) | Auto-deploy from `main` |
| Backend | Railway | `uvicorn main:app --host 0.0.0.0 --port $PORT`, root dir `backend/` |
| Cache | In-memory (Python dict, 200 entries) | Redis optional via `REDIS_URL` |
| Analytics DB | Postgres (optional) | `DATABASE_URL` env var on Railway |

### Required Railway env vars
```
GOOGLE_PLACES_API_KEY=...
ANTHROPIC_API_KEY=...          # or USE_CLAUDE_CLI=true for local dev
ALLOWED_ORIGINS=https://hsproperty-analysis.vercel.app
ANALYTICS_TOKEN=...
DATABASE_URL=postgresql://...  # optional but recommended
```

### Network Error root cause & fix
Railway's reverse proxy kills slow requests (>30s) **without** adding CORS headers to the timeout response. The browser then sees a CORS failure and reports "Network Error". 
- Fix applied: `asyncio.timeout(25)` around full pipeline + Overpass per-request timeout capped at 8s
- If a new external service is added, **always add `timeout=` to every `requests.get()` / `httpx.get()` call**

---

## New components (2026-05-21)

| File | Purpose |
|------|---------|
| `frontend/src/components/CitySelector.tsx` | City picker for multi-city support (staging) |
| `frontend/src/components/MadridElevatorRisk.tsx` | Madrid-specific ITE elevator risk flag |
| `frontend/src/components/MadridITERiskFlag.tsx` | Madrid ITE inspection expiry flag |
| `marketing/card{1-4}-*.html` | Social media preview cards (zh) |

---

## City-Aware Architecture (2026-05-22)

### How city detection works

1. **Geocoder** (`backend/services/geocoder.py`) extracts `city`, `region`, `country_code` from Nominatim address components. Returns `"barcelona"` or `"madrid"` or `None` (unsupported).
2. **Bounding box guard**: If detected city but coordinates outside that city's bbox → resets city to None and downgrades geocode confidence.
3. **`analyze.py`** passes `city` through to ALL city-specific functions.

### City-specific function signatures (all accept `city: str | None`)
- `calculate_acquisition_costs(price, city=)` — ITP/AJD rates
- `estimate_hidden_costs(prop, price, city=)` — IBI rate
- `estimate_seller_economics(price, ..., city=)` — Plusvalía rate
- `get_district_from_address(addr, city=)` — returns None for non-BCN
- `get_safety_data(lat, lng, district)` — returns null indices when district=None
- `get_neighbourhood_trajectory(lat, lng, district, city=)` — skips BCN API for non-BCN
- `get_airbnb_saturation(lat, lng, district, city=)` — uses Madrid heuristics for Madrid
- `get_parking_analysis(lat, lng, district, ..., city=)` — skips Area Verda for non-BCN
- `generate_disclosures(..., city=)` — gates BCN-specific disclosures

### What's still BCN-only (by design)
- **Safety scoring**: Open Data BCN crime indices. Madrid returns null (no data source yet).
- **Neighbourhood trajectory**: BCN Licences API. Madrid returns null (no equivalent API).
- **Fotocasa comparables**: Only tested/calibrated for BCN districts.
- **Area Verda parking**: BCN-only, correctly skipped for Madrid.

### Adding a new city
1. Add city to `_CITY_VIEWBOXES` and `_STATE_TO_CITY` / `_CITY_TO_CITY` in geocoder.py
2. Add ITP/AJD rates to `transaction_costs.py`
3. Add IBI rate to `IBI_RATES` dict
4. Add district price table to `ine.py`
5. Add Airbnb heuristics to `airbnb_saturation.py`
6. Add Plusvalía rate to `_PLUSVALIA_TAX_RATES`
7. Add safety data source or leave null (safe degradation)

### Tax law accuracy (verified 2026-05-22)
- Catalunya ITP: flat 10% (≤€600k) | 11% (€600k–€900k) | 12% (€900k–€1.5M) | 13% (>€1.5M) per DL5/2025
- Madrid ITP: flat 6% (Comunidad de Madrid)
- Catalunya AJD (new build): 1.5%
- Madrid AJD (new build): 0.75%
- Barcelona IBI: 0.66% of cadastral value
- Madrid IBI: 0.456% of cadastral value
- Plusvalía coefficient: RDL 26/2021 table (1yr=0.14, 10yr=0.08, 20yr=0.45)
- Plusvalía land fraction: 0.65 (urban Spain)
- BCN tipo de gravamen: 30% | Madrid: 29%
- IRNR non-resident annual tax: cadastral × 1.1% × 19% ≈ 0.2% of cadastral
- 3% IRNR withholding on purchase price (Modelo 211)
