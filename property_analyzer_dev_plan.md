# Property Analyzer — Development Notes

> Architecture, scoring rationale, and implementation decisions. For setup and usage, see [README.md](README.md).

---

## Current state (2026-05-09)

Phase 1–5 complete. Full stack running locally. All 7 scoring dimensions implemented and tested against real Barcelona addresses.

**Running services:**
- Redis: `docker compose up redis`
- Backend: `cd backend && uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`

---

## Scoring design decisions

### Why "missing data = neutral, not negative"

Catastro often lacks year_built, energy_cert, and surface_m2 for properties — especially older buildings where records weren't digitised. This is normal in Spain. Treating null as "bad" produces false red flags in the AI narrative and inflates hidden-cost warnings. The fix: all scoring modules use district-average neutral values when a specific data point is absent, and the AI prompt explicitly prohibits listing missing cadastral data as a risk.

### Why floor level adjusts noise

Noise is a function of physical distance to the source — vertically as well as horizontally. Street-level bar noise attenuates significantly with height due to building reflection and distance. Each floor above ground adds ~5 points to the noise score (cap: +40 at ≈8th floor). This was validated empirically: a 7th-floor resident next to 12 bars reported no perceived noise, matching the revised score of ~84/100.

### Why bars count positively in Convenience

Bars, pubs, and cafes are included in OSM's `amenity=bar|pub|cafe|restaurant` category. They contribute to evening accessibility and urban vibrancy — the same reason walkability scores value them. In the noise model, only `amenity=nightclub` is weighted heavily (−30 pts each, distance-weighted). Regular bars get a much smaller penalty (−10 pts, distance-weighted) that can be partially offset by floor-level bonus.

### Why logarithmic POI saturation

A neighbourhood with 50 supermarkets is not meaningfully better than one with 8. The original linear formula (`count × 20`) gave Eixample absurdly high convenience scores purely from POI density. The log-saturation formula `100 × (1 − 1/(1 + count/half_sat))` produces diminishing returns that match real-world experience: 1 pharmacy is a big deal, 10 is only marginally better than 5.

### Why the Overpass User-Agent header matters

Overpass API returns HTTP 406 without a User-Agent header (updated policy as of late 2024). The original code silently swallowed the exception and cached the empty result in Redis for 24h. Fix: add `User-Agent: PropertyAnalyzer/2.0` to all Overpass requests, and call `r.raise_for_status()` so failures surface rather than silently producing empty POI data.

---

## Data source quirks

### Catastro coordinate lookup

The Catastro API (`Consulta_RCCOOR`) returns a building's RC (Referencia Catastral) from lat/lng. This sometimes hits the building centroid rather than a specific unit, so surface_m2 and floor data may reflect the whole building or be absent for multi-unit buildings. When null, scoring falls back to neutral values.

### Inside Airbnb

The Barcelona CSV (~20MB compressed) is downloaded once from `insideairbnb.com/get-the-data/` and cached at `~/.cache/property_analyzer/airbnb_bcn.csv`. The data is quarterly; saturation counts may be 3–6 months stale. Fallback: district-level heuristics.

### INE census section pricing

`get_census_section_from_coords` calls the INE WPS service which is slow and often returns no CUSEC. The district fallback table in `ine.py` covers all 10 Barcelona districts with 2024 median prices. The WPS service is best-effort.

### BCN business licences API

Used for neighbourhood trajectory. The API (`opendata-ajuntament.barcelona.cat`) has variable latency (3–15s). Timeout set to 10s with district fallback. New licence counts are used as a gentrification proxy — not a perfect signal but directionally reliable.

---

## AI narrative: `claude -p` subprocess

See `services/ai_narrative.py`. The pattern is identical to voice_blog's `ClaudeCodeBackend`:

1. System + user prompt are concatenated with XML tags
2. `claude -p --output-format json --model sonnet --fallback-model haiku` is called as a subprocess
3. The JSON wrapper's `result` field is parsed
4. On any failure, a graceful fallback dict is returned (analysis still shows scores)

Key prompt constraints (enforced in `_SYSTEM`):
- Missing cadastral data must NOT be listed as a risk
- Bars/restaurants must NOT be listed as risks unless they are nightclubs
- Floor boost > 20 pts means noise is already adjusted — don't re-penalise
- Risks must be confirmed problems, not data absences

---

## Next work items

- [ ] Manual floor input in AddressInput (for when Catastro returns null)
- [ ] Freemium gate: blur AI narrative + hidden costs for unauthenticated users
- [ ] PDF export (react-to-pdf or print CSS)
- [ ] Property save + price-change alerts (requires auth)
- [ ] Madrid/Valencia support (new safety data source, new district tables)
- [ ] Community meeting minutes upload → AI summary
- [ ] Renovation cost estimator tied to energy cert + surface

---

## Monetisation model

| Tier | Price | Includes |
|------|-------|----------|
| Free | 3/month | Basic scores, POI map, safety, valuation range |
| Standard | €9.99/mo | + AI narrative, hidden costs, Airbnb saturation, school quality |
| Pro | €19.99/mo | + Unlimited, compare tool, PDF export, alerts |
| B2B Agent | €99/mo/seat | White-label PDF, bulk API, custom branding |
