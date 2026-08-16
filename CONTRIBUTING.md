# Contributing

Thanks for looking at this project. It's no longer under active commercial development (see the "Project status" note in [README.md](README.md)), but PRs and issues are welcome — maintenance is best-effort.

## Before you start

- For anything beyond a typo fix, open an issue first describing what you want to change. Saves both of us the round trip if it's out of scope or already planned.
- Read `CLAUDE.md` in the repo root. It documents a real quality incident from early development (10 "done" features shipped with 18 bugs, 3 of which crashed every request in production) and the review protocol adopted afterward. That protocol applies to human contributors too, not just AI agents.

## The short version of the review protocol

Any change that touches a new endpoint, a new component, or a data model:

1. **Code review before running anything** — check dict iteration guards against non-list values, Pydantic `Optional` types match what the service actually returns, and frontend `fetch()` URLs match the Vite proxy config and the FastAPI route.
2. **Test with real numbers** — start the backend, curl the endpoint, and check the output makes domain sense (e.g. a €450k property should never need €500k cash to buy). Don't trust fast mental math on financial calculations — write out the formula with a concrete example.
3. **Second pass** — re-check the items in step 1 with fresh eyes, plus a final `py_compile` / `tsc --noEmit` check.

## Tax and legal data

This project encodes real Spanish tax law (ITP, AJD, IBI, Plusvalía rates for Barcelona, Madrid, and Valencia). If you're touching `backend/services/transaction_costs.py`, `ine.py`, or `disclosures.py`, cite an official source (BOE, `atc.gencat.cat`, `sede.catastro.gob.es`, etc.) in the PR description. Don't guess at rates — a wrong tax rate is worse than no feature at all.

## What "done" means

- [ ] Python syntax check passes (`python -m py_compile` on modified files)
- [ ] `npx tsc --noEmit` passes (frontend changes)
- [ ] Backend starts without errors (`uvicorn main:app --reload`)
- [ ] New/changed endpoints tested with `curl` against realistic inputs
- [ ] Output values sanity-checked by hand, not just "the code ran"
- [ ] Edge cases considered: what happens when an external API (Catastro, Overpass, Fotocasa) is down or returns nothing?

"Tests pass" isn't "done" if there are no tests for the new code path. This project doesn't have a full test suite yet — manual verification via curl is the current baseline. Adding real tests for a module you touch is always welcome.

## Setup

See the [Quick start](README.md#quick-start-local-dev) section in the README. Copy `backend/.env.example` to `backend/.env` — you'll need at minimum a `GOOGLE_PLACES_API_KEY` (free tier) to run the backend locally.

## Code style

- Backend: standard FastAPI/Pydantic patterns, async I/O in `services/`, pure functions with no I/O in `scoring/`.
- Frontend: TypeScript, functional React components, strings live in `frontend/src/i18n/strings.ts` (English + Chinese — please add both if you add UI copy).
- No new abstractions for one-off cases. Three similar lines beats a premature helper.
