import type { ValuationData, PropertyData } from '../types/analysis'
import WaterfallChart from './WaterfallChart'
import SourceBadge from './SourceBadge'
import { useLanguage } from '../contexts/LanguageContext'

interface Props { valuation: ValuationData; listingPrice?: number; property?: PropertyData }

const VERDICT_STYLES: Record<string, { bg: string; text: string }> = {
  undervalued:             { bg: 'bg-green-50', text: 'text-green-700' },
  fair:                    { bg: 'bg-blue-50',  text: 'text-blue-700'  },
  overpriced:              { bg: 'bg-amber-50', text: 'text-amber-700' },
  significantly_overpriced:{ bg: 'bg-red-50',   text: 'text-red-700'   },
}

const fmt = (n: number) => `€${n.toLocaleString('es-ES')}`

export default function ValuationModule({ valuation, listingPrice, property }: Props) {
  const { t } = useLanguage()
  const val = t.sections.valuation
  const style = VERDICT_STYLES[valuation.verdict] ?? VERDICT_STYLES.fair

  const missing: string[] = []
  if (!property?.surface_m2) missing.push(t.form.surface)
  if (!property?.year_built)  missing.push(t.form.yearBuilt)
  if (!property?.energy_cert) missing.push(t.form.energyCert)

  return (
    <div className="card p-5 space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{val.label}</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{val.title}</h3>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="text-center p-3 bg-stone-50 rounded-xl border" style={{ borderColor: 'var(--border)' }}>
          <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{val.base}</p>
          <p className="text-lg font-bold font-display" style={{ color: 'var(--text-main)' }}>{fmt(valuation.base_value)}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{fmt(valuation.fair_value_ppm2)}/m²</p>
        </div>
        <div className="text-center p-3 bg-blue-50 rounded-xl border border-blue-100">
          <p className="text-xs text-blue-600 mb-1">{val.fair}</p>
          <p className="text-lg font-bold font-display text-blue-700">{fmt(valuation.fair_value)}</p>
          <p className="text-xs text-blue-400">
            {fmt(valuation.fair_value_low)} – {fmt(valuation.fair_value_high)}
          </p>
        </div>
        {listingPrice && (
          <div className={`text-center p-3 rounded-xl ${style.bg}`}>
            <p className={`text-xs mb-1 ${style.text}`}>{val.listing}</p>
            <p className={`text-lg font-bold font-display ${style.text}`}>{fmt(listingPrice)}</p>
            {valuation.vs_listing_pct != null && (
              <p className={`text-xs ${style.text}`}>
                {valuation.vs_listing_pct > 0 ? '+' : ''}{valuation.vs_listing_pct.toFixed(1)}% vs fair
              </p>
            )}
          </div>
        )}
      </div>

      <div className={`px-4 py-3 rounded-lg ${style.bg}`}>
        <span className={`font-semibold ${style.text}`}>{(val.verdicts as Record<string, string>)[valuation.verdict]}</span>
        <span className="text-sm ml-2" style={{ color: 'var(--text-muted)' }}>
          {val.confidence} {(valuation.confidence * 100).toFixed(0)}%
        </span>
      </div>

      {missing.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
          <span className="font-semibold">{val.defaultsWarning}</span> — {val.defaultsMissing}{' '}
          {missing.join(', ')}.{' '}
          {val.defaultsAdd}
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
