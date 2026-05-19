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
import { useLanguage } from '../contexts/LanguageContext'

interface Props { data: AnalyzeResponse }

export default function Report({ data }: Props) {
  const { t } = useLanguage()

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="space-y-5" id="report-root">
      {/* Address header + PDF button */}
      <div className={`card p-5 ${data.geocode_confidence === 'low' ? 'bg-amber-50 border-amber-200' : ''}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{t.report.analysisFor}</p>
            <h2 className="text-base font-semibold leading-snug" style={{ color: 'var(--text-main)' }}>{data.address}</h2>
          </div>
          <button
            onClick={handlePrint}
            className="shrink-0 flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border transition-all hover:opacity-80 print:hidden"
            style={{ borderColor: 'var(--border)', color: 'var(--text-sub)' }}
            title="Print or save as PDF"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {t.report.savePdf}
          </button>
        </div>

        {data.geocode_warning && (
          <div className="mt-3 flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            <span className="text-amber-500 text-sm shrink-0">⚠</span>
            <p className="text-xs text-amber-700 leading-relaxed">
              <span className="font-semibold">{t.report.addressMismatch} </span>{data.geocode_warning}
            </p>
          </div>
        )}
        <div className="flex gap-4 mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
          <span>{t.report.reportId} {data.request_id.slice(0, 8)}</span>
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
            listingPrice={data.listing_price}
            property={data.property}
            comparables={data.market_comparables}
            acquisitionCosts={data.acquisition_costs}
            sellerEconomics={data.seller_economics}
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

      <p className="text-xs text-center pb-4" style={{ color: 'var(--text-muted)' }}>
        {t.report.sources} {data.data_sources.join(' · ')}
      </p>
    </div>
  )
}
