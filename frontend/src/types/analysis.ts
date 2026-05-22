export interface PoiItem {
  name: string;
  distance_m: number;
  category: string;
  lat?: number;
  lng?: number;
  google_rating?: number;
  google_reviews?: number;
  routes: string[];
}

export interface PoiCategory {
  category: string;
  total_count: number;
  top_items: PoiItem[];
  avg_rating?: number;
  total_reviews?: number;
}

export interface SafetyData {
  theft_rate_index: number | null;
  vehicle_crime_index: number | null;
  vandalism_index: number | null;
  night_safety_index: number | null;
  district: string | null;
  data_year: number | null;
}

export interface PropertyData {
  address_normalized: string;
  lat: number;
  lng: number;
  surface_m2?: number;
  year_built?: number;
  energy_cert?: string;
  cadastral_value?: number;
  has_lift?: boolean;
  floor?: number;
  ite_status?: string;
  has_parking?: boolean;
  has_terrace?: boolean;
  has_views?: boolean;
}

export interface GarageEntry {
  name: string;
  distance_m: number;
  monthly_est_eur?: number | null;
}

export interface ParkingStreetSegment {
  zone_type: 'zona_verde' | 'zona_azul' | 'resident' | 'dum';
  distance_m: number;
  location?: string | null;
  tariff?: string | null;
  timetable?: string | null;
  places?: string | null;
  resident_zone?: string | null;
  dum_zone?: string | null;
}

export interface ParkingData {
  has_private_parking: boolean;
  nearby_garages_count: number;
  nearby_garages: GarageEntry[];
  nearby_garages_unpriced?: GarageEntry[];
  nearby_garages_unpriced_count?: number;
  zone_type: 'zona_verde' | 'zona_azul' | 'resident' | 'dum' | 'free' | 'mixed' | 'unknown';
  zone_monthly_eur?: number | null;
  street_tariff?: string | null;
  street_timetable?: string | null;
  resident_zone?: string | null;
  official_segments: ParkingStreetSegment[];
  official_data_last_modified?: string | null;
  official_source_url?: string | null;
  recommended_option: 'private' | 'garage' | 'street' | 'free' | 'unknown';
  recommended_monthly_eur?: number | null;
  parking_needed: boolean;
}

export interface ValuationAdjustment {
  name: string;
  multiplier: number;
  impact_eur: number;
  source: string;
}

export interface ValuationData {
  base_value: number;
  fair_value: number;
  fair_value_low: number;
  fair_value_high: number;
  fair_value_ppm2: number;
  adjustments: ValuationAdjustment[];
  confidence: number;
  vs_listing_pct?: number;
  verdict: string;
}

export interface AirbnbSaturationData {
  tourist_pct_building?: number | null;
  tourist_count_500m: number | null;
  tourist_count_100m: number | null;
  risk_label: 'low' | 'medium' | 'high' | 'very_high';
  data_source: string;
}

export interface SchoolEntry {
  name: string;
  distance_m: number;
  school_type: 'public' | 'concertada' | 'private';
  language: string;
  google_rating?: number;
  composite_score: number;
}

export interface SchoolQualityData {
  nearest_school_m?: number;
  school_type?: string;
  language?: string;
  google_rating?: number;
  composite_score: number;
  schools: SchoolEntry[];
}

export interface NoiseData {
  day_noise_score: number;
  night_noise_score: number;
  weekend_noise_score: number;
  bars_clubs_500m: number;
  nightclubs_500m: number;
  floor_boost_applied: number;
  construction_risk: string;
  night_data_note?: string;
}

export interface HiddenCostsData {
  ibi_annual_eur: number;
  community_fee_monthly_eur: number;
  utility_estimate_monthly_eur: number;
  derrama_risk_label: 'low' | 'medium' | 'high';
  derrama_provision_monthly_eur: number;
  energy_upgrade_required: boolean;
  energy_upgrade_estimate_eur?: number;
  parking_monthly_eur?: number;
  total_monthly_eur: number;
  total_annual_eur: number;
}

export interface NeighbourhoodTrajectoryData {
  trend: 'rising' | 'stable' | 'declining' | null;
  new_businesses_12m: number | null;
  renovation_permits_12m: number | null;
  trend_score: number | null;
}

export interface NarrativeData {
  verdict: string;
  summary: string;
  key_risks: string[];
  key_positives: string[];
  negotiation_angle: string;
  generated_by: string;
}

export interface DimensionScore {
  name: string;
  score: number;
  weight: number;
  sub_scores: Record<string, number>;
}

export interface CompositeScore {
  composite: number;
  composite_pre_penalty: number;
  grade: string;
  confidence: number;
  penalty_multipliers: Record<string, number>;
  dimensions: DimensionScore[];
}

export interface ComparableListing {
  price: number;
  size: number;
  ppm2: number;
}

export interface MarketComparables {
  median_ppm2: number;
  p25_ppm2: number;
  p75_ppm2: number;
  listings: ComparableListing[];
  count?: number;
  source: string;
  district: string;
  size_range: string;
  asking_ppm2?: number;
  position?: 'well_below' | 'below' | 'within_range' | 'above' | 'well_above';
}

export interface AcquisitionCostsData {
  listing_price: number;
  is_new_build: boolean;
  transfer_tax: number;
  transfer_tax_label: string;
  notary_est: number;
  registry_est: number;
  gestoria_est: number;
  other_fees: number;
  total: number;
  overhead_pct: number;
  min_down_payment: number;
  min_savings_needed: number;
}

export interface SellerEconomicsData {
  listing_price: number;
  agency_low: number;
  agency_high: number;
  plusvalia_est?: number;
  years_owned_est: number;
  energy_cert_cost: number;
  seller_costs_low: number;
  seller_costs_high: number;
  seller_floor_low: number;
  seller_floor_high: number;
  negotiation_headroom_pct: number;
}

export interface DisclosureItem {
  id: string;
  severity: 'red' | 'yellow' | 'green' | 'info';
  category: 'costs' | 'building' | 'legal' | 'neighborhood';
  title: string;
  detail: string;
  action?: string;
}

export interface AnalyzeResponse {
  request_id: string;
  address: string;
  lat: number;
  lng: number;
  listing_price?: number;
  geocode_confidence: 'high' | 'low';
  geocode_warning?: string;
  city?: 'barcelona' | 'madrid' | 'valencia' | null;
  property: PropertyData;
  disclosures: DisclosureItem[];
  poi_categories: PoiCategory[];
  safety: SafetyData;
  airbnb_saturation: AirbnbSaturationData;
  school_quality: SchoolQualityData;
  noise: NoiseData;
  neighbourhood_trajectory: NeighbourhoodTrajectoryData;
  valuation: ValuationData;
  market_comparables?: MarketComparables;
  acquisition_costs?: AcquisitionCostsData;
  seller_economics?: SellerEconomicsData;
  hidden_costs: HiddenCostsData;
  parking?: ParkingData;
  score: CompositeScore;
  negotiation_tips: string[];
  narrative: NarrativeData;
  data_sources: string[];
  analysis_cost_usd: number;
}

export interface UserAnswers {
  children_age?:       'none' | 'young' | 'teen'
  stay_duration?:      'short' | 'medium' | 'long'
  has_car?:            boolean
  rental_intent?:      'none' | 'long_term' | 'short_term'
  noise_tolerance?:    'love_it' | 'neutral' | 'need_quiet'
  work_situation?:     'home' | 'commute' | 'retired'
  renovation_appetite?:'ready' | 'minor' | 'move_in_ready'
  lifestyle_priority?: 'important' | 'neutral' | 'not_important'
}

export interface AnalyzeRequest {
  address: string;
  listing_price?: number;
  buyer_profile: 'balanced' | 'family' | 'investor' | 'retiree' | 'expat';
  user_answers?: UserAnswers;
  year_built?: number;
  floor?: number;
  surface_m2?: number;
  energy_cert?: string;
  condition?: 'renovated' | 'good' | 'needs_work';
  has_parking?: boolean;
  has_terrace?: boolean;
  has_views?: boolean;
  language?: string;
  city_hint?: 'barcelona' | 'madrid' | 'valencia';
}

export interface CompareAnalysis {
  address: string;
  listing_price?: number;
  composite_score: number;
  grade: string;
  fair_value: number;
  vs_listing_pct?: number;
  hidden_costs_monthly: number;
  airbnb_risk: string;
  school_score: number;
  safety_score: number;
  key_risks: string[];
  key_positives: string[];
}

export interface CompareNarrative {
  recommendation: string;
  summary: string;
  winner_by_dimension: Record<string, string>;
}

export interface CompareResponse {
  buyer_profile: string;
  analyses: CompareAnalysis[];
  comparison: CompareNarrative;
}

export interface CompareRequest {
  addresses: string[];
  listing_prices?: number[];
  buyer_profile: string;
}
