import type { ValuationData, PropertyData, MarketComparables } from '../types/analysis'
import WaterfallChart from './WaterfallChart'
import SourceBadge from './SourceBadge'
import { useLanguage } from '../contexts/LanguageContext'

interface Props {
  valuation: ValuationData
  listingPrice?: number
  property?: PropertyData
  comparables?: MarketComparables
}

const fmt  = (n: number) => `€${n.toLocaleString('es-ES')}`
const fmtK = (n: number) => n >= 1000 ? `€${Math.round(n / 1000)}k` : `€${n}`

const POSITION_LABEL: Record<string, { text: string; color: string }> = {
  well_below:    { text: 'Well below market',  color: 'text-blue-700'  },
  below:         { text: 'Below market',        color: 'text-blue-600'  },
  within_range:  { text: 'Within market range', color: 'text-green-700' },
  above:         { text: 'Above market',        color: 'text-amber-700' },
  well_above:    { text: 'Well above market',   color: 'text-red-700'   },
}

function MarketRangeBar({ comp }: { comp: MarketComparables }) {
  // Build a normalised position (0-1) for the price dot on the bar
  // Bar spans from p25*0.7 to p75*1.5 for visual context
  const lo = comp.p25_ppm2 * 0.6
  const hi = comp.p75_ppm2 * 1.6
  const range = hi - lo

  const pct = (v: number) => Math.max(0, Math.min(100, ((v - lo) / range) * 100))

  const p25pct    = pct(comp.p25_ppm2)
  const medpct    = pct(comp.median_ppm2)
  const p75pct    = pct(comp.p75_ppm2)
  const askpct    = comp.asking_ppm2 ? pct(comp.asking_ppm2) : null

  const posLabel  = comp.position ? POSITION_LABEL[comp.position] : null

  return (
    <div className="space-y-3">
      {/* position summary */}
      {askpct !== null && posLabel && comp.asking_ppm2 && (
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className={`text-sm font-semibold ${posLabel.color}`}>{posLabel.text}</span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            asking {fmt(comp.asking_ppm2)}/m² · district median {fmt(comp.median_ppm2)}/m²
          </span>
        </div>
      )}

      {/* range bar */}
      <div className="relative h-7">
        {/* grey track */}
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-2 bg-stone-200 rounded-full" />

        {/* IQR band (p25→p75) */}
        <div
          className="absolute top-1/2 -translate-y-1/2 h-2 bg-blue-200 rounded-full"
          style={{ left: `${p25pct}%`, width: `${p75pct - p25pct}%` }}
        />

        {/* median tick */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-0.5 h-4 bg-blue-500 rounded-full"
          style={{ left: `${medpct}%` }}
        />

        {/* asking price dot */}
        {askpct !== null && (
          <div
            className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-white shadow-md bg-amber-500 z-10"
            style={{ left: `calc(${askpct}% - 8px)` }}
          />
        )}
      </div>

      {/* axis labels */}
      <div className="flex justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
        <span>{fmtK(comp.p25_ppm2)}/m² <span className="opacity-60">(P25)</span></span>
        <span className="font-medium text-blue-600">{fmtK(comp.median_ppm2)}/m² median</span>
        <span>{fmtK(comp.p75_ppm2)}/m² <span className="opacity-60">(P75)</span></span>
      </div>
    </div>
  )
}

export default function ValuationModule({ valuation, listingPrice, property, comparables }: Props) {
  const { t } = useLanguage()
  const val = t.sections.valuation

  const missing: string[] = []
  if (!property?.surface_m2) missing.push(t.form.surface)
  if (!property?.year_built)  missing.push(t.form.yearBuilt)
  if (!property?.energy_cert) missing.push(t.form.energyCert)

  const hasComparables = comparables && (comparables.median_ppm2 > 0)

  return (
    <div className="card p-5 space-y-5">

      {/* ── Market Context (primary, shown when comparables available) ── */}
      {hasComparables && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-widest mb-0.5" style={{ color: 'var(--accent)' }}>
                MARKET CONTEXT
              </p>
              <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>
                Similar properties in {comparables.district}
              </h3>
            </div>
            <span className="text-xs px-2 py-1 rounded-full bg-stone-100 border" style={{ color: 'var(--text-muted)', borderColor: 'var(--border)' }}>
              {comparables.size_range} · {comparables.source}
              {comparables.count ? ` · ${comparables.count} listings` : ''}
            </span>
          </div>

          <MarketRangeBar comp={comparables} />

          {/* Comparable listings table */}
          {comparables.listings.length > 0 && (
            <div className="border rounded-xl overflow-hidden" style={{ borderColor: 'var(--border)' }}>
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-stone-50 border-b" style={{ borderColor: 'var(--border)' }}>
                    <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>Price</th>
                    <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>Size</th>
                    <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--text-muted)' }}>€/m²</th>
                  </tr>
                </thead>
                <tbody>
                  {comparables.listings.map((l, i) => (
                    <tr key={i} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                      <td className="px-3 py-2 font-medium" style={{ color: 'var(--text-main)' }}>{fmt(l.price)}</td>
                      <td className="px-3 py-2 text-right" style={{ color: 'var(--text-muted)' }}>{l.size} m²</td>
                      <td className="px-3 py-2 text-right font-medium" style={{ color: 'var(--text-main)' }}>€{l.ppm2.toLocaleString('es-ES')}</td>
                    </tr>
                  ))}
                  {listingPrice && property?.surface_m2 && (
                    <tr className="bg-amber-50">
                      <td className="px-3 py-2 font-semibold text-amber-800">{fmt(listingPrice)} <span className="font-normal text-amber-600">(asking)</span></td>
                      <td className="px-3 py-2 text-right text-amber-700">{property.surface_m2} m²</td>
                      <td className="px-3 py-2 text-right font-semibold text-amber-800">
                        €{Math.round(listingPrice / property.surface_m2).toLocaleString('es-ES')}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── INE Fair Value estimate (secondary / reference) ── */}
      <div className={hasComparables ? 'border-t pt-4' : ''} style={hasComparables ? { borderColor: 'var(--border)' } : {}}>
        <div className="mb-3">
          <p className="text-xs font-medium uppercase tracking-widest mb-0.5" style={{ color: 'var(--accent)' }}>
            {hasComparables ? 'REGISTRY REFERENCE' : val.label}
          </p>
          <h3 className="font-semibold text-sm" style={{ color: 'var(--text-main)' }}>
            {hasComparables
              ? 'INE registry estimate (may underestimate market by 30–50%)'
              : val.title}
          </h3>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-stone-50 rounded-xl border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{val.base}</p>
            <p className="text-base font-bold font-display" style={{ color: 'var(--text-main)' }}>{fmt(valuation.base_value)}</p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{fmt(valuation.fair_value_ppm2)}/m²</p>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-xl border border-blue-100">
            <p className="text-xs text-blue-600 mb-1">{val.fair}</p>
            <p className="text-base font-bold font-display text-blue-700">{fmt(valuation.fair_value)}</p>
            <p className="text-xs text-blue-400">
              {fmt(valuation.fair_value_low)} – {fmt(valuation.fair_value_high)}
            </p>
          </div>
          {listingPrice && (
            <div className="text-center p-3 rounded-xl bg-stone-50 border" style={{ borderColor: 'var(--border)' }}>
              <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{val.listing}</p>
              <p className="text-base font-bold font-display" style={{ color: 'var(--text-main)' }}>{fmt(listingPrice)}</p>
            </div>
          )}
        </div>

        {missing.length > 0 && (
          <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
            <span className="font-semibold">{val.defaultsWarning}</span> — {val.defaultsMissing}{' '}
            {missing.join(', ')}.{' '}
            {val.defaultsAdd}
          </div>
        )}

        <WaterfallChart base={valuation.base_value} adjustments={valuation.adjustments} fair={valuation.fair_value} />
      </div>

      <SourceBadge className="mt-1" sources={[
        ...(hasComparables && comparables!.source === 'Fotocasa'
          ? [{ label: 'Fotocasa', url: 'https://www.fotocasa.es', note: 'active listings' }]
          : hasComparables
          ? [{ label: 'District statistics', url: 'https://www.fotocasa.es/es/indice-de-precios', note: '2024 calibrated ranges' }]
          : []),
        { label: 'INE — median price/m²', url: 'https://www.ine.es/jaxiT3/Tabla.htm?t=25171', note: 'by census section' },
        { label: 'Catastro', url: 'https://www.catastro.meh.es/', note: 'surface, year built' },
      ]} />
    </div>
  )
}
