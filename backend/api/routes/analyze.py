import asyncio
import os
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from models.request import AnalyzeRequest, CompareRequest
from models.response import (
    AnalyzeResponse, CompareResponse, CompareAnalysis, CompareNarrative,
    PropertyData, SafetyData, ValuationData, CompositeScore, DimensionScore,
    PoiCategory, PoiItem,
    AirbnbSaturationData, SchoolQualityData, SchoolEntry, NoiseData,
    HiddenCostsData, NeighbourhoodTrajectoryData, NarrativeData,
    DisclosureItem, MarketComparables, ComparableListing,
    AcquisitionCostsData, SellerEconomicsData,
    ParkingData, GarageEntry,
)
from services import geocoder, overpass, google_places, catastro, ine, open_data_bcn
from services import airbnb_saturation, school_quality, noise_ecosystem, neighbourhood_trajectory
from services import ai_narrative, disclosures, fotocasa_scraper
from services.parking import get_parking_analysis
from scoring import engine, valuation
from scoring.hidden_costs import estimate_hidden_costs
from scoring.transaction_costs import calculate_acquisition_costs, estimate_seller_economics
from utils.cache import cached
from utils.rate_limiter import check_rate_limit, get_client_ip
from utils import analytics, dashboard as dashboard_util

router = APIRouter()


# ─── helpers ────────────────────────────────────────────────────────────────

def _format_poi_categories(enriched: dict) -> list[PoiCategory]:
    result = []
    for cat, items in enriched.items():
        # Transit: show more stops for map rendering; school: show top 5; others: top 3
        n = 8 if cat in ("bus_stop", "metro") else 5 if cat == "school" else 3
        top_n = items[:n]
        rated = [i for i in top_n[:3] if i.get("google_rating") is not None]
        avg_rating    = round(sum(i["google_rating"] for i in rated) / len(rated), 1) if rated else None
        total_reviews = sum(i.get("google_reviews") or 0 for i in rated) or None
        poi_items = [
            PoiItem(
                name=p["name"],
                distance_m=p["distance_m"],
                category=cat,
                lat=p.get("lat"),
                lng=p.get("lng"),
                google_rating=p.get("google_rating"),
                google_reviews=p.get("google_reviews"),
                routes=p.get("routes", []),
            )
            for p in top_n
        ]
        result.append(PoiCategory(
            category=cat,
            total_count=len(items),
            top_items=poi_items,
            avg_rating=avg_rating,
            total_reviews=total_reviews,
        ))
    return result


def _generate_negotiation_tips(val: dict, score: dict, prop: dict, language: str = "en") -> list[str]:
    tips = []
    delta = val.get("vs_listing_pct") or 0
    zh = language == "zh"

    # Note: delta is INE-based; only surface as a tip when comparables confirm the signal
    # (comparables are the primary price signal — see market.py price_fairness)
    if delta > 10:
        tips.append(
            f"INE数据显示挂牌价偏高约 {delta:.0f}%，建议结合Fotocasa可比房源数据综合判断议价空间。"
            if zh else
            f"Registry data suggests the asking price may be {delta:.0f}% above area norms. "
            "Cross-reference with the Fotocasa comparables above before making an offer."
        )

    cert = (prop.get("energy_cert") or "").strip().upper()
    if cert in ("E", "F", "G"):
        tips.append(
            f"能耗证书 {cert} 级，根据西班牙2033年节能强制令需进行改造，预计费用 €9,000–€28,000，可作为议价筹码。"
            if zh else
            f"Energy cert {cert} will require upgrades under Spain's 2033 efficiency mandate. "
            "Estimated cost €9,000–€28,000 — use this as a negotiation lever."
        )

    year = prop.get("year_built")
    if year and 1960 <= year < 1975:
        tips.append(
            '楼房建于1960–1975年"发展年代"，是铝水泥（aluminosis）和石棉风险最高的建造时期，签订定金合同前务必要求专业结构检测报告。'
            if zh else
            "Building dates from the 1960–1975 'desarrollismo' era — highest risk period "
            "for aluminosis (alumina cement) and asbestos. Request a specialist structural "
            "survey before signing arras."
        )
    elif year and (2026 - year) > 45 and prop.get("ite_status") != "FAVORABLE":
        tips.append(
            "楼龄超过45年，ITE（建筑技术检查）状态未经确认，签约前索取ITE报告，将不确定性作为议价依据。"
            if zh else
            "Building over 45 years old without a confirmed favourable ITE inspection. "
            "Request the ITE report before signing arras — use uncertainty as leverage."
        )

    if delta <= -5:
        tips.append(
            "房价低于周边可比市场，仍可就任何结构或文件问题进行议价。"
            if zh else
            "Property appears undervalued vs. neighbourhood comparables. "
            "Still negotiate on any structural or documentation issues found."
        )

    return tips or [
        "价格基本合理，重点应放在索取ITE报告和产权调查上。" if zh
        else "Property appears fairly priced. Focus due diligence on ITE report and title search."
    ]


@cached(ttl=86400)
async def _run_full_analysis(
    address: str,
    listing_price: float | None,
    buyer_profile: str,
    user_answers_json: str | None,
    year_built_override: int | None = None,
    floor_override: int | None = None,
    surface_m2_override: float | None = None,
    energy_cert_override: str | None = None,
    condition_override: str | None = None,
    language: str = "en",
    has_parking_override: bool | None = None,
    has_terrace_override: bool | None = None,
    has_views_override: bool | None = None,
) -> dict:
    """Core analysis pipeline — used by both /analyze and /compare."""
    from models.user_profile import UserAnswers
    answers = UserAnswers.model_validate_json(user_answers_json) if user_answers_json else None

    try:
        geo = await geocoder.geocode(address)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    lat, lng = geo["lat"], geo["lng"]
    district = open_data_bcn.get_district_from_address(geo["address"])

    # Step 1: Parallel data fetch (all IO-bound tasks)
    (
        poi_raw, prop_data, safety_data, census_section,
        airbnb_data, trajectory_data,
    ) = await asyncio.gather(
        overpass.fetch_pois(lat, lng),
        catastro.get_property_data(lat, lng),
        open_data_bcn.get_safety_data(lat, lng, district),
        ine.get_census_section_from_coords(lat, lng),
        airbnb_saturation.get_airbnb_saturation(lat, lng, district),
        neighbourhood_trajectory.get_neighbourhood_trajectory(lat, lng, district),
    )

    # Step 1b: Market comparables (parallel, non-blocking — failure just omits the section)
    try:
        surface_for_comp = (
            surface_m2_override
            or (prop_data.get("surface_m2") if prop_data else None)
        )
        comparables_data = await fotocasa_scraper.get_market_comparables(
            district=district,
            surface_m2=surface_for_comp,
            listing_price=listing_price,
        )
    except Exception:
        comparables_data = None

    # Apply manual overrides when Catastro returns null
    overrides: dict = {}
    if year_built_override is not None and prop_data.get("year_built") is None:
        overrides["year_built"] = year_built_override
    if floor_override is not None and prop_data.get("floor") is None:
        overrides["floor"] = floor_override
    if surface_m2_override is not None and prop_data.get("surface_m2") is None:
        overrides["surface_m2"] = surface_m2_override
    if energy_cert_override is not None and prop_data.get("energy_cert") is None:
        overrides["energy_cert"] = energy_cert_override.upper()
    if condition_override == "renovated":
        overrides["renovated"] = True
    # Apply unconditionally — Catastro never provides these
    if has_parking_override is not None:
        overrides["has_parking"] = has_parking_override
    if has_terrace_override is not None:
        overrides["has_terrace"] = has_terrace_override
    if has_views_override is not None:
        overrides["has_views"] = has_views_override
    if overrides:
        prop_data = {**prop_data, **overrides}

    # Step 2: OSM baseline ratings (replaces Google Places — zero cost) + parking in parallel
    enriched_poi, parking_data = await asyncio.gather(
        google_places.enrich_with_ratings(poi_raw),
        get_parking_analysis(
            lat=lat,
            lng=lng,
            district=district,
            has_private_parking=bool(prop_data.get("has_parking")),
            has_car=bool(answers.has_car) if answers else False,
        ),
    )

    # Step 3: INE price data
    median_ppm2 = await ine.get_median_price_ppm2(census_section or "", district)

    # Step 4: Synchronous derivations (no IO)
    valuation_data    = valuation.estimate_fair_value(median_ppm2, prop_data, listing_price)
    _parking_m = (
        parking_data["recommended_monthly_eur"]
        if parking_data["parking_needed"] and parking_data["recommended_monthly_eur"]
        else None
    )
    hidden_costs_data = estimate_hidden_costs(prop_data, listing_price, parking_monthly=_parking_m)
    school_data       = school_quality.get_school_quality(poi_raw, enriched_poi)
    noise_data        = noise_ecosystem.get_noise_ecosystem(poi_raw, prop_data)

    # Derive price fairness from Fotocasa comparables position (reliable market data).
    # Fall back to INE-based delta only when comparables unavailable.
    _comp_position = comparables_data.get("position") if comparables_data else None
    _comp_position_score = {
        "well_below":   100,
        "below":         80,
        "within_range":  65,
        "above":         45,
        "well_above":    20,
    }.get(_comp_position) if _comp_position else None

    market_data = {
        "annual_growth_pct":      4.2,
        "days_on_market":         55,
        "vs_fair_value_pct":      valuation_data.get("vs_listing_pct", 0),
        "comparables_position_score": _comp_position_score,
        "rental_yield":           0.042,
        "city_avg_yield":         0.045,
    }

    # Transaction cost data (buyer + seller)
    acq_costs_data    = calculate_acquisition_costs(listing_price) if listing_price else None
    seller_econ_data  = estimate_seller_economics(
        listing_price,
        cadastral_value=prop_data.get("cadastral_value"),
    ) if listing_price else None

    score_data = engine.calculate_composite(
        poi_raw, enriched_poi, safety_data,
        prop_data, valuation_data, market_data,
        school_data, noise_data, trajectory_data,
        hidden_costs_data, airbnb_data,
        user_answers=answers,
        legacy_profile=buyer_profile,
    )

    disclosure_items = disclosures.generate_disclosures(
        prop_data=prop_data,
        airbnb_data=airbnb_data,
        noise_data=noise_data,
        hidden_costs_data=hidden_costs_data,
        trajectory_data=trajectory_data,
        school_data=school_data,
        listing_price=listing_price,
        buyer_profile=buyer_profile,
        language=language,
    )

    analysis_flat = {
        "address":                  geo["display_name"],
        "lat":                      lat,
        "lng":                      lng,
        "property":                 prop_data,
        "safety":                   safety_data,
        "airbnb_saturation":        airbnb_data,
        "school_quality":           school_data,
        "noise":                    noise_data,
        "neighbourhood_trajectory": trajectory_data,
        "valuation":                valuation_data,
        "acquisition_costs":        acq_costs_data,
        "seller_economics":         seller_econ_data,
        "hidden_costs":             hidden_costs_data,
        "parking":                  parking_data,
        "score":                    score_data,
        "disclosures":              disclosure_items,
        "enriched_poi":             enriched_poi,
        "poi_raw":                  poi_raw,
    }

    narrative_data = ai_narrative.generate_narrative(analysis_flat, buyer_profile, language=language)

    return {
        **analysis_flat,
        "geo":              geo,
        "district":         district,
        "census_section":   census_section,
        "negotiation_tips":  _generate_negotiation_tips(valuation_data, score_data, prop_data, language=language),
        "narrative":         narrative_data,
        "listing_price":     listing_price,
        "comparables":       comparables_data,
    }


# ─── endpoints ──────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, request: Request):
    ip = get_client_ip(request)
    allowed, remaining = await check_rate_limit(ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="You have used all 5 free analyses for today. Come back tomorrow for more.",
        )

    user_answers_json = req.user_answers.model_dump_json() if req.user_answers else None
    _t0 = time.time()
    data = await _run_full_analysis(
        req.address, req.listing_price, req.buyer_profile,
        user_answers_json, req.year_built, req.floor,
        req.surface_m2, req.energy_cert, req.condition,
        language=req.language,
        has_parking_override=req.has_parking,
        has_terrace_override=req.has_terrace,
        has_views_override=req.has_views,
    )
    duration_ms = round((time.time() - _t0) * 1000)

    lat, lng      = data["lat"], data["lng"]
    prop_data     = data["property"]
    valuation_data = data["valuation"]
    safety_data   = data["safety"]
    airbnb_data   = data["airbnb_saturation"]
    school_data   = data["school_quality"]
    noise_data    = data["noise"]
    trajectory_data = data["neighbourhood_trajectory"]
    hidden_costs_data = data["hidden_costs"]
    score_data    = data["score"]
    narrative_data   = data["narrative"]
    comparables_data = data.get("comparables")
    geo              = data["geo"]

    prop_response = PropertyData(
        address_normalized=prop_data.get("address_normalized") or geo["display_name"],
        lat=lat, lng=lng,
        surface_m2=prop_data.get("surface_m2"),
        year_built=prop_data.get("year_built"),
        energy_cert=prop_data.get("energy_cert"),
        orientation=prop_data.get("orientation"),
        cadastral_value=prop_data.get("cadastral_value"),
        has_lift=prop_data.get("has_lift"),
        floor=prop_data.get("floor"),
        ite_status=prop_data.get("ite_status", "UNKNOWN"),
        flood_zone=prop_data.get("flood_zone"),
        open_charges=prop_data.get("open_charges"),
        has_parking=prop_data.get("has_parking"),
        has_terrace=prop_data.get("has_terrace"),
        has_views=prop_data.get("has_views"),
    )

    enriched_count = sum(
        min(3, len(pois)) for pois in data["enriched_poi"].values()
        if any(p.get("google_rating") is not None for p in pois[:3])
    )

    request_id = str(uuid.uuid4())
    _score_dims = {d["name"]: d.get("score") for d in score_data.get("dimensions", [])}
    _user_ans   = req.user_answers.model_dump(exclude_none=True) if req.user_answers else {}
    analytics.log_analysis(
        ip=ip,
        address=geo["display_name"],
        score=score_data["composite"],
        disclosures_count=len(data.get("disclosures", [])),
        request_id=request_id,
        district=data.get("district", ""),
        listing_price=req.listing_price,
        buyer_profile=req.buyer_profile,
        language=req.language,
        duration_ms=duration_ms,
        fotocasa_success=bool(comparables_data and comparables_data.get("source") == "Fotocasa"),
        user_answers=_user_ans,
        score_dimensions=_score_dims,
    )

    return AnalyzeResponse(
        request_id=request_id,
        address=geo["display_name"],
        lat=lat, lng=lng,
        listing_price=req.listing_price,
        geocode_confidence=geo.get("geocode_confidence", "high"),
        geocode_warning=geo.get("geocode_warning"),
        property=prop_response,
        disclosures=[DisclosureItem(**d) for d in data.get("disclosures", [])],
        poi_categories=_format_poi_categories(data["enriched_poi"]),
        safety=SafetyData(**safety_data),
        airbnb_saturation=AirbnbSaturationData(**airbnb_data),
        school_quality=SchoolQualityData(
            nearest_school_m=school_data.get("nearest_school_m"),
            school_type=school_data.get("school_type"),
            language=school_data.get("language"),
            google_rating=school_data.get("google_rating"),
            composite_score=school_data.get("composite_score", 50.0),
            schools=[SchoolEntry(**s) for s in school_data.get("schools", [])],
        ),
        noise=NoiseData(**noise_data),
        neighbourhood_trajectory=NeighbourhoodTrajectoryData(**trajectory_data),
        valuation=ValuationData(
            base_value=valuation_data["base_value"],
            fair_value=valuation_data["fair_value"],
            fair_value_low=valuation_data["fair_value_low"],
            fair_value_high=valuation_data["fair_value_high"],
            fair_value_ppm2=valuation_data["fair_value_ppm2"],
            adjustments=valuation_data["adjustments"],
            confidence=valuation_data["confidence"],
            vs_listing_pct=valuation_data.get("vs_listing_pct"),
            verdict=valuation_data.get("verdict", "unknown"),
        ),
        market_comparables=(
            MarketComparables(
                median_ppm2=comparables_data["median_ppm2"],
                p25_ppm2=comparables_data["p25_ppm2"],
                p75_ppm2=comparables_data["p75_ppm2"],
                listings=[ComparableListing(**l) for l in comparables_data.get("listings", [])],
                count=comparables_data.get("count"),
                source=comparables_data["source"],
                district=comparables_data["district"],
                size_range=comparables_data["size_range"],
                asking_ppm2=comparables_data.get("asking_ppm2"),
                position=comparables_data.get("position"),
            )
            if comparables_data else None
        ),
        acquisition_costs=(
            AcquisitionCostsData(**data["acquisition_costs"])
            if data.get("acquisition_costs") else None
        ),
        seller_economics=(
            SellerEconomicsData(**data["seller_economics"])
            if data.get("seller_economics") else None
        ),
        hidden_costs=HiddenCostsData(**hidden_costs_data),
        parking=ParkingData(
            has_private_parking=data["parking"]["has_private_parking"],
            nearby_garages_count=data["parking"]["nearby_garages_count"],
            nearby_garages=[GarageEntry(**g) for g in data["parking"]["nearby_garages"]],
            zone_type=data["parking"]["zone_type"],
            zone_monthly_eur=data["parking"]["zone_monthly_eur"],
            recommended_option=data["parking"]["recommended_option"],
            recommended_monthly_eur=data["parking"]["recommended_monthly_eur"],
            parking_needed=data["parking"]["parking_needed"],
        ) if data.get("parking") else None,
        score=CompositeScore(
            composite=score_data["composite"],
            composite_pre_penalty=score_data["composite_pre_penalty"],
            grade=score_data["grade"],
            confidence=score_data["confidence"],
            penalty_multipliers=score_data["penalty_multipliers"],
            dimensions=[
                DimensionScore(
                    name=d["name"],
                    score=d["score"],
                    weight=d["weight"],
                    sub_scores=d["sub_scores"],
                    sub_weights=d.get("sub_weights", {}),
                    coverage=d.get("coverage", 1.0),
                )
                for d in score_data["dimensions"]
            ],
        ),
        negotiation_tips=data["negotiation_tips"],
        narrative=NarrativeData(
            verdict=narrative_data.get("verdict", ""),
            summary=narrative_data.get("summary", ""),
            key_risks=narrative_data.get("key_risks", []),
            key_positives=narrative_data.get("key_positives", []),
            negotiation_angle=narrative_data.get("negotiation_angle", ""),
            generated_by=narrative_data.get("generated_by", "claude-code-subscription"),
        ),
        data_sources=[
            "Nominatim", "Overpass API", "OSM Baseline Ratings",
            "Catastro", "INE", "Open Data BCN",
            "Inside Airbnb", "BCN Licences API", "Claude Code",
        ],
        analysis_cost_usd=0.0,
    )


@router.post("/compare", response_model=CompareResponse)
async def compare(req: CompareRequest):
    if len(req.addresses) < 2 or len(req.addresses) > 3:
        raise HTTPException(status_code=422, detail="Provide 2 or 3 addresses to compare.")

    prices = req.listing_prices or [None] * len(req.addresses)
    if len(prices) < len(req.addresses):
        prices += [None] * (len(req.addresses) - len(prices))

    analyses = await asyncio.gather(*[
        _run_full_analysis(addr, price, req.buyer_profile, None)
        for addr, price in zip(req.addresses, prices)
    ])

    labels = [f"Property {chr(65 + i)}" for i in range(len(analyses))]

    compare_analyses = []
    for i, data in enumerate(analyses):
        score_data  = data["score"]
        val_data    = data["valuation"]
        safe_score  = next(
            (d["score"] or 0 for d in score_data["dimensions"] if d["name"] == "Safety"), 0
        )
        compare_analyses.append(CompareAnalysis(
            address=labels[i],
            listing_price=data["listing_price"],
            composite_score=score_data["composite"],
            grade=score_data["grade"],
            fair_value=val_data["fair_value"],
            vs_listing_pct=val_data.get("vs_listing_pct"),
            hidden_costs_monthly=data["hidden_costs"]["total_monthly_eur"],
            airbnb_risk=data["airbnb_saturation"]["risk_label"],
            school_score=data["school_quality"]["composite_score"],
            safety_score=safe_score,
            key_risks=data["narrative"].get("key_risks", []),
            key_positives=data["narrative"].get("key_positives", []),
        ))

    comparison_input = {
        "buyer_profile": req.buyer_profile,
        "properties": [
            {
                "label":                labels[i],
                "address":              data["address"],
                "composite_score":      compare_analyses[i].composite_score,
                "grade":                compare_analyses[i].grade,
                "vs_listing_pct":       compare_analyses[i].vs_listing_pct,
                "hidden_costs_monthly": compare_analyses[i].hidden_costs_monthly,
                "airbnb_risk":          compare_analyses[i].airbnb_risk,
                "school_score":         compare_analyses[i].school_score,
                "safety_score":         compare_analyses[i].safety_score,
                "key_risks":            compare_analyses[i].key_risks,
                "key_positives":        compare_analyses[i].key_positives,
            }
            for i, data in enumerate(analyses)
        ],
    }

    narr = ai_narrative.generate_comparison_narrative(comparison_input)

    return CompareResponse(
        buyer_profile=req.buyer_profile,
        analyses=compare_analyses,
        comparison=CompareNarrative(
            recommendation=narr.get("recommendation", ""),
            summary=narr.get("summary", ""),
            winner_by_dimension=narr.get("winner_by_dimension", {}),
        ),
    )


@router.get("/admin/analytics", response_class=HTMLResponse)
async def get_analytics_dashboard(token: str = ""):
    expected = os.getenv("ANALYTICS_TOKEN", "")
    if not expected or token != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    stats = analytics.get_stats()
    return HTMLResponse(content=dashboard_util.render(stats, token=token))


@router.get("/admin/analytics/json")
async def get_analytics_json(token: str = ""):
    expected = os.getenv("ANALYTICS_TOKEN", "")
    if not expected or token != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"summary": analytics.get_summary(), "entries": analytics.get_all()}


class TrackEvent(BaseModel):
    session_id: str
    request_id: str
    event: str
    data: dict = {}


@router.post("/track")
async def track_event(body: TrackEvent):
    analytics.log_track_event(
        session_id=body.session_id,
        request_id=body.request_id,
        event=body.event,
        data=body.data,
    )
    return {"ok": True}
