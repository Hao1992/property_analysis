import type { AnalyzeResponse } from '../types/analysis'
import ScoreCard from '../components/ScoreCard'
import NeighborhoodModule from '../components/NeighborhoodModule'
import SafetyModule from '../components/SafetyModule'
import ValuationModule from '../components/ValuationModule'
import NegotiationTips from '../components/NegotiationTips'
import PropertyMap from '../components/PropertyMap'
import PropertyDetails from '../components/PropertyDetails'
import NarrativeCard from '../components/NarrativeCard'
import HiddenCostBreakdown from '../components/HiddenCostBreakdown'
import AirbnbSaturation from '../components/AirbnbSaturation'
import SchoolQualityModule from '../components/SchoolQualityModule'
import NoiseEcosystem from '../components/NoiseEcosystem'
import NeighbourhoodTrajectory from '../components/NeighbourhoodTrajectory'
import DisclosureSection from '../components/DisclosureSection'

interface Props { data: AnalyzeResponse }

export default function Report({ data }: Props) {
  return (
    <div className="space-y-5">
      {/* Address header */}
      <div className={`border rounded-2xl p-5 ${data.geocode_confidence === 'low' ? 'bg-yellow-950 border-yellow-700' : 'bg-slate-800 border-slate-700'}`}>
        <p className="text-xs text-slate-400 mb-1">Analysis for</p>
        <h2 className="text-base font-semibold text-white leading-snug">{data.address}</h2>
        {data.geocode_warning && (
          <div className="mt-3 flex items-start gap-2 bg-yellow-900/50 border border-yellow-700 rounded-lg px-3 py-2">
            <span className="text-yellow-400 text-sm shrink-0">⚠️</span>
            <p className="text-xs text-yellow-200 leading-relaxed">
              <span className="font-semibold">Address mismatch: </span>{data.geocode_warning}
            </p>
          </div>
        )}
        <div className="flex gap-4 mt-2 text-xs text-slate-500">
          <span>ID: {data.request_id.slice(0, 8)}</span>
        </div>
      </div>

      {/* Disclosures — what to know before signing */}
      <DisclosureSection items={data.disclosures ?? []} />

      {/* AI Narrative — hero element */}
      <NarrativeCard
        narrative={data.narrative}
        grade={data.score.grade}
        composite={data.score.composite}
      />

      {/* Score + map row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <ScoreCard score={data.score} />
        </div>
        <PropertyMap lat={data.lat} lng={data.lng} address={data.address} poiCategories={data.poi_categories} />
      </div>

      {/* Property details */}
      <PropertyDetails property={data.property} />

      {/* Valuation + Hidden costs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {data.valuation && (
          <ValuationModule
            valuation={data.valuation}
            listingPrice={undefined}
            property={data.property}
          />
        )}
        <HiddenCostBreakdown data={data.hidden_costs} />
      </div>

      {/* Negotiation */}
      <NegotiationTips tips={data.negotiation_tips} />

      {/* Safety + Airbnb */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <SafetyModule safety={data.safety} />
        <AirbnbSaturation data={data.airbnb_saturation} />
      </div>

      {/* School + Noise */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <SchoolQualityModule
          data={data.school_quality}
          schoolCategory={data.poi_categories.find(c => c.category === 'school')}
        />
        <NoiseEcosystem data={data.noise} />
      </div>

      {/* Neighbourhood trajectory */}
      <NeighbourhoodTrajectory data={data.neighbourhood_trajectory} />

      {/* POIs */}
      <NeighborhoodModule categories={data.poi_categories} lat={data.lat} lng={data.lng} />

      <p className="text-xs text-slate-500 text-center pb-4">
        Sources: {data.data_sources.join(' · ')}
      </p>
    </div>
  )
}
