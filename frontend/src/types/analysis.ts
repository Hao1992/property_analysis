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
  theft_rate_index: number;
  vehicle_crime_index: number;
  vandalism_index: number;
  night_safety_index: number;
  district: string;
  data_year: number;
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
  tourist_pct_building?: number;
  tourist_count_500m: number;
  tourist_count_100m: number;
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
}

export interface HiddenCostsData {
  ibi_annual_eur: number;
  community_fee_monthly_eur: number;
  utility_estimate_monthly_eur: number;
  derrama_risk_label: 'low' | 'medium' | 'high';
  derrama_provision_monthly_eur: number;
  energy_upgrade_required: boolean;
  energy_upgrade_estimate_eur?: number;
  total_monthly_eur: number;
  total_annual_eur: number;
}

export interface NeighbourhoodTrajectoryData {
  trend: 'rising' | 'stable' | 'declining';
  new_businesses_12m: number;
  renovation_permits_12m: number;
  trend_score: number;
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
  geocode_confidence: 'high' | 'low';
  geocode_warning?: string;
  property: PropertyData;
  disclosures: DisclosureItem[];
  poi_categories: PoiCategory[];
  safety: SafetyData;
  airbnb_saturation: AirbnbSaturationData;
  school_quality: SchoolQualityData;
  noise: NoiseData;
  neighbourhood_trajectory: NeighbourhoodTrajectoryData;
  valuation: ValuationData;
  hidden_costs: HiddenCostsData;
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
  language?: string;
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
