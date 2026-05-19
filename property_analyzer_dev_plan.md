# Beyond Price — Development Notes

> Architecture decisions, scoring rationale, and implementation history. For setup and usage, see [README.md](README.md).

---

## Current state (2026-05-20)

Full stack running locally. All 8 scoring dimensions implemented. Analytics pipeline live.

**Recent shipped work:**
- Acquisition cost calculator (ITP + notary + registry → total cash needed + min savings)
- Seller economics panel (agency commission + plusvalía → seller floor + negotiation headroom %)
- Fotocasa market comparables replace INE fair value as primary price signal
- `price_fairness` scoring dimension now uses Fotocasa position, not INE delta
- Full Chinese (中文) i18n across all components and backend output
- Analytics pipeline: extended event log + HTML dashboard + frontend IntersectionObserver tracking
- Pre-purchase disclosures module (4–6 actionable items per report)
- 8-question UserAnswers questionnaire replacing static buyer profiles

**Running services:**
- Backend: `cd backend && uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`
- Redis: `docker compose up redis` (optional — cache degrades gracefully without it)

---

## Scoring design decisions

### Why "missing data = neutral, not negative"

Catastro often lacks year_built, energy_cert, and surface_m2 for properties — especially older buildings where records weren't digitised. This is normal in Spain. Treating null as "bad" produces false red flags in the AI narrative and inflates hidden-cost warnings. Fix: all scoring modules use district-average neutral values when a specific data point is absent, and the AI prompt explicitly prohibits listing missing cadastral data as a risk.

### Why Fotocasa comparables replaced INE fair value

The INE median price/m² (census section level) consistently underestimates the Barcelona market by 30–50%. This caused every fair-value estimate to show the listing as 30–40% overpriced — which was noise, not signal. The resulting ±12% range (e.g. €588k–€748k for a €580k property) was too wide to be actionable.

Fotocasa comparables are real active listings filtered by district and size range. They tell you where the asking price sits relative to today's market, which is what buyers actually need. The price_fairness sub-score in the Market dimension now uses the comparables position directly:
- `well_below` (asking < P25 × 0.85) → 100
- `below` (asking < P25) → 80
- `within_range` (P25 ≤ asking ≤ P75) → 65
- `above` (asking ≤ P75 × 1.3) → 45
- `well_above` → 20

INE data is retained as a background reference in `valuation.py` but is not shown in the UI.

### Why seller economics instead of a fair value verdict

The old "Fair value: €668k (±€80k)" card was removed. The range was too wide and the number was wrong. Instead, we answer the two questions buyers actually have:

1. **How much do I need?** → Acquisition cost breakdown (ITP + notary + registry = total out-of-pocket, minimum savings required)
2. **How much can I negotiate?** → Seller economics (agency 3–5% + plusvalía est. + energy cert = seller floor price, headroom %)

This shifts the tool from "trying to value property" (unreliable) to "helping you understand the deal structure" (concrete and actionable).

### Why floor level adjusts noise

Noise is a function of physical distance to the source — vertically as well as horizontally. Street-level bar noise attenuates significantly with height due to building reflection and distance. Each floor above ground adds ~5 points to the noise score (cap: +40 at ≈8th floor). Validated empirically: a 7th-floor resident next to 12 bars reported no perceived noise, matching the revised score of ~84/100.

### Why bars count positively in Convenience

Bars, pubs, and cafes contribute to evening accessibility and urban vibrancy. In the noise model, only `amenity=nightclub` is weighted heavily (−30 pts each, distance-weighted). Regular bars get a much smaller noise penalty (−10 pts, distance-weighted) that can be partially offset by the floor-level bonus.

### Why logarithmic POI saturation

A neighbourhood with 50 supermarkets is not meaningfully better than one with 8. The log-saturation formula `100 × (1 − 1/(1 + count/half_sat))` produces diminishing returns that match real-world experience.

### Why the Overpass User-Agent header matters

Overpass API returns HTTP 406 without a User-Agent header (updated policy as of late 2024). The original code silently swallowed the exception and cached the empty result in Redis for 24h. Fix: add `User-Agent: PropertyAnalyzer/2.0` to all Overpass requests, and call `r.raise_for_status()` so failures surface rather than silently producing empty POI data.

---

## Analytics pipeline

### What is collected

Each analysis event (in `pa_analytics.jsonl`) captures:

```
ts, request_id, ip_hash (SHA-256 prefix), address, district,
composite_score, disclosures_count, price_bucket, has_price,
buyer_profile, language, duration_ms, fotocasa_success,
user_answers (dict), score_dimensions (dict), error (null or string)
```

Frontend behaviour events (in `pa_events.jsonl`) capture:

```
ts, session_id (sessionStorage UUID), request_id, event, data
```

Event types: `report_viewed`, `section_view`, `section_dwell` (>2s), `language_switch`, `pdf_download`.

### Dashboard

`GET /admin/analytics?token=<ANALYTICS_TOKEN>` returns a self-contained HTML page generated by `utils/dashboard.py`. No external service needed. Uses Chart.js from CDN. Shows:
- Summary cards: total, today, week, unique IPs, avg score, Fotocasa rate, P50 duration, PDF downloads
- DAU bar chart (14 days)
- Score distribution histogram
- District + price range + language breakdown
- API health (Fotocasa success rate, P50/P95 duration)
- Section view heatmap (frontend tracking)
- Buyer profile distribution
- Recent 20 analyses table

### Session ID

Each browser session gets a UUID from `sessionStorage` (`bp_sid`). Not persisted across sessions. Not sent to any third party. Used only to correlate frontend events with analysis results within a session.

---

## Data source quirks

### Fotocasa scraper

`services/fotocasa_scraper.py` fetches active listings by district and surface range. The scraper relies on Fotocasa's cookie-based session (`FOTOCASA_COOKIES` in `.env`). If the cookie expires, comparables fall back to district statistics. The `fotocasa_success` flag in each analytics event makes it easy to monitor scraper health from the dashboard.

### Catastro coordinate lookup

The Catastro API (`Consulta_RCCOOR`) returns a building's RC from lat/lng. This sometimes hits the building centroid rather than a specific unit, so `surface_m2` and `floor` data may reflect the whole building or be absent for multi-unit buildings. When null, scoring falls back to neutral values.

### Inside Airbnb

The Barcelona CSV (~20MB compressed) is downloaded once from `insideairbnb.com/get-the-data/` and cached at `~/.cache/property_analyzer/airbnb_bcn.csv`. The data is quarterly; saturation counts may be 3–6 months stale. Fallback: district-level heuristics.

### INE census section pricing

`get_census_section_from_coords` calls the INE WPS service which is slow and often returns no CUSEC. The district fallback table in `ine.py` covers all 10 Barcelona districts with 2024 median prices. This data is used only as a background reference in `valuation.py` — not displayed in the UI.

### BCN business licences API

Used for neighbourhood trajectory. The API (`opendata-ajuntament.barcelona.cat`) has variable latency (3–15s). Timeout set to 10s with district fallback.

---

## AI narrative

See `services/ai_narrative.py`. The pattern is identical to voice_blog's `ClaudeCodeBackend`:

1. System + user prompt concatenated with XML tags
2. `claude -p --output-format json --model sonnet --fallback-model haiku` called as subprocess
3. JSON wrapper's `result` field parsed
4. On any failure, graceful fallback dict returned (analysis still shows scores)

Key prompt constraints:
- Missing cadastral data must NOT be listed as a risk
- Bars/restaurants must NOT be listed as risks unless they are nightclubs
- Floor boost > 20 pts means noise is already adjusted — don't re-penalise
- Risks must be confirmed problems, not data absences
- Chinese output when `language="zh"` is requested

---

## Transaction cost calculations

`scoring/transaction_costs.py` implements two functions used in the report but kept out of the scoring engine (they're informational, not scored):

**`calculate_acquisition_costs(listing_price, is_new_build=False)`**
- Catalunya ITP: 10% (resale), or IVA 10% + AJD 1.5% (new build)
- Notary: `min(2500, max(700, price × 0.0015 + 600))`
- Registry: `min(1500, max(300, price × 0.0006 + 200))`
- Gestoria: €350 fixed
- Returns total cash needed, overhead %, minimum savings (20% down + all costs)

**`estimate_seller_economics(listing_price, cadastral_value, years_owned_est=10)`**
- Agency: 3–5% of asking price
- Plusvalía (Barcelona objective method): `land_value × coeff × 0.28` where `land_value = cadastral_value × 0.35` and `coeff ≈ 0.17` for 10 years
- Energy certificate: €200 fixed
- Returns seller floor range and negotiation headroom %

Both are computed only when `listing_price` is provided. Plusvalía requires `cadastral_value` from Catastro; the estimate is omitted from the display when it's not available.

---

## Next work items

- [ ] `is_new_build` flag in `AnalyzeRequest` (acquisition costs currently default to resale ITP)
- [ ] Freemium gate — blur AI narrative + hidden costs for unauthenticated users; 5/day limit is the free tier
- [ ] PDF export page (print CSS exists; dedicated `/report/:id` shareable URL)
- [ ] Property save + price-change alerts (requires auth layer)
- [ ] Madrid and Valencia support (new safety data source, new district tables)
- [ ] Renovation cost estimator (energy cert + surface + condition → cost range)
- [ ] Community meeting minutes upload → AI summary

---

## Monetisation model

| Tier | Price | Includes |
|------|-------|----------|
| Free | 5/day (no account) | All scores, POI map, safety, market comparables, acquisition cost |
| Standard | €9.99/mo | + AI narrative, hidden costs, Airbnb saturation, school quality, seller economics |
| Pro | €19.99/mo | + Unlimited, compare tool, PDF export, alerts |
| B2B Agent | €99/mo/seat | White-label PDF, bulk API, custom branding |
