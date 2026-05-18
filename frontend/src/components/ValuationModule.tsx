import type { ValuationData, PropertyData } from '../types/analysis'
import WaterfallChart from './WaterfallChart'
import SourceBadge from './SourceBadge'

interface Props { valuation: ValuationData; listingPrice?: number; property?: PropertyData }

const VERDICT_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  undervalued:             { bg: 'bg-green-50', text: 'text-green-700', label: '🟢 Undervalued' },
  fair:                    { bg: 'bg-blue-50',  text: 'text-blue-700',  label: '🔵 Fairly priced' },
  overpriced:              { bg: 'bg-amber-50', text: 'text-amber-700', label: '🟡 Overpriced' },
  significantly_overpriced:{ bg: 'bg-red-50',   text: 'text-red-700',   label: '🔴 Significantly overpriced' },
}

const fmt = (n: number) => `€${n.toLocaleString('es-ES')}`

export default function ValuationModule({ valuation, listingPrice, property }: Props) {
  const style = VERDICT_STYLES[valuation.verdict] ?? VERDICT_STYLES.fair

  const missing: string[] = []
  if (!property?.surface_m2) missing.push('surface area (using 80m² estimate)')
  if (!property?.year_built)  missing.push('year built')
  if (!property?.energy_cert) missing.push('energy certificate (defaulting to D)')

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">Fair Value Estimate</h2>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-4 bg-gray-50 rounded-xl">
          <p className="text-xs text-gray-500 mb-1">Base value</p>
          <p className="text-xl font-bold text-gray-800">{fmt(valuation.base_value)}</p>
          <p className="text-xs text-gray-400">{fmt(valuation.fair_value_ppm2)}/m²</p>
        </div>
        <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-100">
          <p className="text-xs text-blue-600 mb-1">Fair value</p>
          <p className="text-xl font-bold text-blue-700">{fmt(valuation.fair_value)}</p>
          <p className="text-xs text-blue-400">
            {fmt(valuation.fair_value_low)} – {fmt(valuation.fair_value_high)}
          </p>
        </div>
        {listingPrice && (
          <div className={`text-center p-4 rounded-xl ${style.bg}`}>
            <p className={`text-xs mb-1 ${style.text}`}>Listing price</p>
            <p className={`text-xl font-bold ${style.text}`}>{fmt(listingPrice)}</p>
            {valuation.vs_listing_pct != null && (
              <p className={`text-xs ${style.text}`}>
                {valuation.vs_listing_pct > 0 ? '+' : ''}{valuation.vs_listing_pct.toFixed(1)}% vs fair
              </p>
            )}
          </div>
        )}
      </div>

      <div className={`mb-4 px-4 py-3 rounded-lg ${style.bg}`}>
        <span className={`font-semibold ${style.text}`}>{style.label}</span>
        <span className="text-sm text-gray-500 ml-2">
          Confidence: {(valuation.confidence * 100).toFixed(0)}%
        </span>
      </div>

      {missing.length > 0 && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
          <span className="font-semibold">Estimate uses defaults</span> — Catastro didn't return:{' '}
          {missing.join(', ')}.{' '}
          Add these in the form above for a more accurate estimate.
        </div>
      )}

      <WaterfallChart base={valuation.base_value} adjustments={valuation.adjustments} fair={valuation.fair_value} />
      <SourceBadge className="mt-4" sources={[
        { label: 'INE — median price/m²', url: 'https://www.ine.es/jaxiT3/Tabla.htm?t=25171', note: 'by census section' },
        { label: 'Catastro', url: 'https://www.catastro.meh.es/', note: 'cadastral value, surface, year built' },
      ]} />
    </div>
  )
}
