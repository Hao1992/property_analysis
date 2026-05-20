from pydantic import BaseModel
from typing import Optional


class PoiItem(BaseModel):
    name: str
    distance_m: float
    category: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    google_rating: Optional[float] = None
    google_reviews: Optional[int] = None
    routes: list[str] = []


class PoiCategory(BaseModel):
    category: str
    total_count: int
    top_items: list[PoiItem]
    avg_rating: Optional[float] = None
    total_reviews: Optional[int] = None


class SafetyData(BaseModel):
    theft_rate_index: float
    vehicle_crime_index: float
    vandalism_index: float
    night_safety_index: float
    district: str
    data_year: int


class PropertyData(BaseModel):
    address_normalized: str
    lat: float
    lng: float
    surface_m2: Optional[float] = None
    year_built: Optional[int] = None
    energy_cert: Optional[str] = None
    orientation: Optional[str] = None          # catastro orientation (S/N/E/O/SE/SO/NE/NO)
    cadastral_value: Optional[float] = None
    has_lift: Optional[bool] = None
    floor: Optional[int] = None
    ite_status: Optional[str] = None           # FAVORABLE | DESFAVORABLE | UNKNOWN
    flood_zone: Optional[str] = None           # A | B | C | None
    open_charges: Optional[int] = None         # count of title encumbrances
    has_parking: Optional[bool] = None
    has_terrace: Optional[bool] = None
    has_views: Optional[bool] = None


class ValuationData(BaseModel):
    base_value: float
    fair_value: float
    fair_value_low: float
    fair_value_high: float
    fair_value_ppm2: float
    adjustments: list[dict]
    confidence: float
    vs_listing_pct: Optional[float] = None
    verdict: str


class AirbnbSaturationData(BaseModel):
    tourist_pct_building: Optional[float] = None
    tourist_count_500m: Optional[int] = None
    tourist_count_100m: Optional[int] = None
    risk_label: str                            # low | medium | high | very_high
    data_source: str = "Inside Airbnb"


class SchoolEntry(BaseModel):
    name: str
    distance_m: float
    school_type: str                           # public | concertada | private
    language: str                              # catalan | spanish | english
    google_rating: Optional[float] = None
    composite_score: float


class SchoolQualityData(BaseModel):
    nearest_school_m: Optional[float] = None
    school_type: Optional[str] = None          # public | concertada | private
    language: Optional[str] = None             # catalan | spanish | english | mixed
    google_rating: Optional[float] = None
    composite_score: float                     # 0–100
    schools: list[SchoolEntry] = []            # all scored nearby schools


class NoiseData(BaseModel):
    day_noise_score: float
    night_noise_score: float
    weekend_noise_score: float
    bars_clubs_500m: int
    nightclubs_500m: int = 0
    floor_boost_applied: int = 0
    construction_risk: str                     # low | medium | high


class GarageEntry(BaseModel):
    name: str
    distance_m: float
    monthly_est_eur: int


class ParkingData(BaseModel):
    has_private_parking: bool
    nearby_garages_count: int
    nearby_garages: list[GarageEntry]
    zone_type: str                         # zona_verde | zona_azul | free | mixed
    zone_monthly_eur: Optional[int] = None # None when zone is free
    recommended_option: str                # private | garage | street | free
    recommended_monthly_eur: Optional[int] = None  # None when has_private_parking=True
    parking_needed: bool                   # has_car=True AND has_parking=False


class HiddenCostsData(BaseModel):
    ibi_annual_eur: float
    community_fee_monthly_eur: float
    utility_estimate_monthly_eur: float
    derrama_risk_label: str                    # low | medium | high
    derrama_provision_monthly_eur: float
    energy_upgrade_required: bool
    energy_upgrade_estimate_eur: Optional[float] = None
    parking_monthly_eur: Optional[int] = None
    total_monthly_eur: float
    total_annual_eur: float


class NeighbourhoodTrajectoryData(BaseModel):
    trend: str                                 # rising | stable | declining
    new_businesses_12m: int
    renovation_permits_12m: int
    trend_score: float                         # 0–100


class NarrativeData(BaseModel):
    verdict: str
    summary: str
    key_risks: list[str]
    key_positives: list[str]
    negotiation_angle: str
    generated_by: str = "claude-code-subscription"


class DimensionScore(BaseModel):
    name: str
    score: Optional[float]                          # None when all sub-dims are missing
    weight: float
    sub_scores: dict[str, Optional[float]]          # None = data unavailable
    sub_weights: dict[str, float] = {}              # effective weights used
    coverage: float = 1.0                           # 0.0–1.0 fraction of sub-dims with data


class CompositeScore(BaseModel):
    composite: float
    composite_pre_penalty: float
    grade: str
    confidence: float = 1.0                         # overall data coverage 0.0–1.0
    penalty_multipliers: dict[str, float]
    dimensions: list[DimensionScore]


class ComparableListing(BaseModel):
    price: int
    size: int
    ppm2: int


class MarketComparables(BaseModel):
    median_ppm2: int
    p25_ppm2: int
    p75_ppm2: int
    listings: list[ComparableListing] = []
    count: Optional[int] = None
    source: str                         # "Fotocasa" | "district statistics"
    district: str
    size_range: str
    asking_ppm2: Optional[int] = None
    position: Optional[str] = None     # well_below | below | within_range | above | well_above


class AcquisitionCostsData(BaseModel):
    listing_price: float
    is_new_build: bool
    transfer_tax: float
    transfer_tax_label: str
    notary_est: float
    registry_est: float
    gestoria_est: float
    other_fees: float
    total: float
    overhead_pct: float
    min_down_payment: float
    min_savings_needed: float


class SellerEconomicsData(BaseModel):
    listing_price: float
    agency_low: float
    agency_high: float
    plusvalia_est: Optional[float] = None
    years_owned_est: int
    energy_cert_cost: float
    seller_costs_low: float
    seller_costs_high: float
    seller_floor_low: float
    seller_floor_high: float
    negotiation_headroom_pct: float


class DisclosureItem(BaseModel):
    id: str
    severity: str                    # red | yellow | green | info
    category: str                    # costs | building | legal | neighborhood
    title: str
    detail: str
    action: Optional[str] = None


class AnalyzeResponse(BaseModel):
    request_id: str
    address: str
    lat: float
    lng: float
    listing_price: Optional[float] = None
    geocode_confidence: str = "high"       # high | low
    geocode_warning: Optional[str] = None  # shown in UI when confidence is low
    property: PropertyData
    disclosures: list[DisclosureItem] = []
    poi_categories: list[PoiCategory]
    safety: SafetyData
    airbnb_saturation: AirbnbSaturationData
    school_quality: SchoolQualityData
    noise: NoiseData
    neighbourhood_trajectory: NeighbourhoodTrajectoryData
    valuation: ValuationData
    market_comparables: Optional[MarketComparables] = None
    acquisition_costs: Optional[AcquisitionCostsData] = None
    seller_economics: Optional[SellerEconomicsData] = None
    hidden_costs: HiddenCostsData
    parking: Optional[ParkingData] = None
    score: CompositeScore
    negotiation_tips: list[str]
    narrative: NarrativeData
    data_sources: list[str]
    analysis_cost_usd: float


class CompareAnalysis(BaseModel):
    address: str
    listing_price: Optional[float] = None
    composite_score: float
    grade: str
    fair_value: float
    vs_listing_pct: Optional[float] = None
    hidden_costs_monthly: float
    airbnb_risk: str
    school_score: float
    safety_score: float
    key_risks: list[str]
    key_positives: list[str]


class CompareNarrative(BaseModel):
    recommendation: str
    summary: str
    winner_by_dimension: dict[str, str]


class CompareResponse(BaseModel):
    buyer_profile: str
    analyses: list[CompareAnalysis]
    comparison: CompareNarrative
