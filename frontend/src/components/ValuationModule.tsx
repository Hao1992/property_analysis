import type { ValuationData, PropertyData, MarketComparables, AcquisitionCostsData, SellerEconomicsData } from '../types/analysis'
import SourceBadge from './SourceBadge'
import { useLanguage } from '../contexts/LanguageContext'

interface Props {
  valuation: ValuationData
  listingPrice?: number
  property?: PropertyData
  comparables?: MarketComparables
  acquisitionCosts?: AcquisitionCostsData
  sellerEconomics?: SellerEconomicsData
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
  const lo = comp.p25_ppm2 * 0.6
  const hi = comp.p75_ppm2 * 1.6
  const range = hi - lo

  const pct = (v: number) => Math.max(0, Math.min(100, ((v - lo) / range) * 100))

  const p25pct  = pct(comp.p25_ppm2)
  const medpct  = pct(comp.median_ppm2)
  const p75pct  = pct(comp.p75_ppm2)
  const askpct  = comp.asking_ppm2 ? pct(comp.asking_ppm2) : null
  const posLabel = comp.position ? POSITION_LABEL[comp.position] : null

  return (
    <div className="space-y-3">
      {askpct !== null && posLabel && comp.asking_ppm2 && (
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className={`text-sm font-semibold ${posLabel.color}`}>{posLabel.text}</span>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            asking {fmt(comp.asking_ppm2)}/m² · district median {fmt(comp.median_ppm2)}/m²
          </span>
        </div>
      )}

      <div className="relative h-7">
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-2 bg-stone-200 rounded-full" />
        <div
          className="absolute top-1/2 -translate-y-1/2 h-2 bg-blue-200 rounded-full"
          style={{ left: `${p25pct}%`, width: `${p75pct - p25pct}%` }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-0.5 h-4 bg-blue-500 rounded-full"
          style={{ left: `${medpct}%` }}
        />
        {askpct !== null && (
          <div
            className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-white shadow-md bg-amber-500 z-10"
            style={{ left: `calc(${askpct}% - 8px)` }}
          />
        )}
      </div>

      <div className="flex justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
        <span>{fmtK(comp.p25_ppm2)}/m² <span className="opacity-60">(P25)</span></span>
        <span className="font-medium text-blue-600">{fmtK(comp.median_ppm2)}/m² median</span>
        <span>{fmtK(comp.p75_ppm2)}/m² <span className="opacity-60">(P75)</span></span>
      </div>
    </div>
  )
}

function CostRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`flex justify-between items-center py-1.5 ${highlight ? 'font-semibold' : ''}`}>
      <span className="text-sm" style={{ color: highlight ? 'var(--text-main)' : 'var(--text-muted)' }}>{label}</span>
      <span className="text-sm tabular-nums" style={{ color: highlight ? 'var(--text-main)' : 'var(--text-muted)' }}>{value}</span>
    </div>
  )
}

function AcquisitionPanel({ ac, t }: { ac: AcquisitionCostsData; t: any }) {
  const s = t.sections.valuation.acquisition
  return (
    <div className="border-t pt-4 space-y-3" style={{ borderColor: 'var(--border)' }}>
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-0.5" style={{ color: 'var(--accent)' }}>
          {s.label}
        </p>
        <h3 className="font-semibold text-sm" style={{ color: 'var(--text-main)' }}>{s.title}</h3>
      </div>

      <div className="rounded-xl border divide-y" style={{ borderColor: 'var(--border)' }}>
        <div className="px-4 py-1">
          <CostRow label={s.askingPrice} value={fmt(ac.listing_price)} />
          <CostRow label={`+ ${ac.transfer_tax_label}`} value={`+${fmt(ac.transfer_tax)}`} />
          <CostRow label={`+ ${s.notaryRegistry}`} value={`~${fmt(ac.other_fees)}`} />
        </div>
        <div className="px-4 py-2 bg-stone-50 rounded-b-xl">
          <div className="flex justify-between items-center">
            <span className="text-sm font-bold" style={{ color: 'var(--text-main)' }}>{s.totalCash}</span>
            <div className="text-right">
              <span className="text-base font-bold font-display" style={{ color: 'var(--accent)' }}>{fmt(ac.total)}</span>
              <span className="text-xs ml-1.5" style={{ color: 'var(--text-muted)' }}>(+{ac.overhead_pct}%)</span>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border px-4 py-3 bg-blue-50 border-blue-100 space-y-1">
        <p className="text-xs font-semibold text-blue-700 mb-1.5">{s.minSavingsTitle}</p>
        <CostRow label={s.downPayment} value={fmt(ac.min_down_payment)} />
        <CostRow label={s.purchaseCosts} value={`+${fmt(ac.transfer_tax + ac.other_fees)}`} />
        <div className="flex justify-between items-center pt-1 border-t border-blue-200 mt-1">
          <span className="text-sm font-bold text-blue-800">{s.totalSavings}</span>
          <span className="text-sm font-bold text-blue-800">{fmt(ac.min_savings_needed)}</span>
        </div>
      </div>
    </div>
  )
}

function SellerPanel({ se, t }: { se: SellerEconomicsData; t: any }) {
  const s = t.sections.valuation.seller
  return (
    <div className="border-t pt-4 space-y-3" style={{ borderColor: 'var(--border)' }}>
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-0.5" style={{ color: 'var(--accent)' }}>
          {s.label}
        </p>
        <h3 className="font-semibold text-sm" style={{ color: 'var(--text-main)' }}>{s.title}</h3>
      </div>

      <div className="rounded-xl border divide-y" style={{ borderColor: 'var(--border)' }}>
        <div className="px-4 py-1">
          <CostRow label={s.agency} value={`${fmt(se.agency_low)} – ${fmt(se.agency_high)}`} />
          {se.plusvalia_est != null && (
            <CostRow label={s.plusvalia} value={`~${fmt(se.plusvalia_est)}`} />
          )}
          <CostRow label={s.energyCert} value={`~${fmt(se.energy_cert_cost)}`} />
        </div>
        <div className="px-4 py-2 bg-stone-50 rounded-b-xl space-y-1.5">
          <div className="flex justify-between items-center">
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.sellerCosts}</span>
            <span className="text-xs font-medium" style={{ color: 'var(--text-main)' }}>
              {fmt(se.seller_costs_low)} – {fmt(se.seller_costs_high)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-bold" style={{ color: 'var(--text-main)' }}>{s.sellerFloor}</span>
            <span className="text-sm font-bold" style={{ color: 'var(--text-main)' }}>
              {fmt(se.seller_floor_low)} – {fmt(se.seller_floor_high)}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200">
        <div className="text-lg">🤝</div>
        <div>
          <span className="text-xs font-semibold text-amber-800">{s.headroom} </span>
          <span className="text-xs font-bold text-amber-900">~{se.negotiation_headroom_pct}%</span>
          <p className="text-xs text-amber-700 mt-0.5">{s.headroomNote}</p>
        </div>
      </div>

      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.irpfNote}</p>
    </div>
  )
}

export default function ValuationModule({ listingPrice, property, comparables, acquisitionCosts, sellerEconomics }: Props) {
  const { t } = useLanguage()
  const hasComparables = comparables && (comparables.median_ppm2 > 0)

  return (
    <div className="card p-5 space-y-5">

      {/* ── Market Context (primary) ── */}
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

      {/* ── Acquisition Cost ── */}
      {acquisitionCosts && (
        <AcquisitionPanel ac={acquisitionCosts} t={t} />
      )}

      {/* ── Seller Economics ── */}
      {sellerEconomics && (
        <SellerPanel se={sellerEconomics} t={t} />
      )}

      <SourceBadge className="mt-1" sources={[
        ...(hasComparables && comparables!.source === 'Fotocasa'
          ? [{ label: 'Fotocasa', url: 'https://www.fotocasa.es', note: 'active listings' }]
          : hasComparables
          ? [{ label: comparables!.source ?? 'District statistics', url: 'https://www.idealista.com/news/', note: '2024 calibrated ranges' }]
          : []),
        { label: 'Catastro', url: 'https://www.catastro.meh.es/', note: 'cadastral value, surface' },
      ]} />
    </div>
  )
}
