import type { ValuationAdjustment as Adjustment } from '../types/analysis'

interface Props {
  base: number
  adjustments: Adjustment[]
  fair: number
}

const fmt = (n: number) => `€${Math.round(n).toLocaleString('es-ES')}`

export default function WaterfallChart({ base, adjustments, fair }: Props) {
  // Only show adjustments with meaningful impact
  const significant = adjustments.filter(a => Math.abs(a.impact_eur) > 10)

  // Max absolute impact for bar scaling
  const maxImpact = Math.max(...significant.map(a => Math.abs(a.impact_eur)), 1)
  const totalAdj  = fair - base
  const totalPct  = ((totalAdj / base) * 100).toFixed(1)

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">How we reached the fair value</h3>

      {/* Base row */}
      <div className="flex items-center gap-3 py-1.5">
        <div className="w-44 shrink-0 text-xs text-gray-500">Base (median ₠/m²)</div>
        <div className="flex-1" />
        <div className="text-sm font-semibold text-gray-700 w-28 text-right">{fmt(base)}</div>
      </div>

      {/* Adjustment rows */}
      {significant.map((adj, i) => {
        const pct     = ((adj.impact_eur / base) * 100)
        const barPct  = Math.round((Math.abs(adj.impact_eur) / maxImpact) * 100)
        const isPos   = adj.impact_eur >= 0
        return (
          <div key={i} className="flex items-center gap-3 py-0.5">
            <div className="w-44 shrink-0 text-xs text-gray-600 truncate" title={adj.name}>{adj.name}</div>
            <div className="flex-1 flex items-center gap-1">
              {!isPos && <div className="flex-1 flex justify-end">
                <div
                  className="h-3 rounded-l bg-red-400"
                  style={{ width: `${barPct}%` }}
                />
              </div>}
              <div className="w-px h-4 bg-gray-300 shrink-0" />
              {isPos && <div className="flex-1">
                <div
                  className="h-3 rounded-r bg-green-400"
                  style={{ width: `${barPct}%` }}
                />
              </div>}
            </div>
            <div className={`text-xs font-medium w-28 text-right ${isPos ? 'text-green-600' : 'text-red-600'}`}>
              {isPos ? '+' : ''}{fmt(adj.impact_eur)} ({isPos ? '+' : ''}{pct.toFixed(1)}%)
            </div>
          </div>
        )
      })}

      {/* Divider */}
      <div className="border-t border-gray-200 my-1" />

      {/* Fair value row */}
      <div className="flex items-center gap-3 py-1.5 bg-blue-50 rounded-lg px-2">
        <div className="w-44 shrink-0 text-sm font-semibold text-blue-700">Fair value estimate</div>
        <div className="flex-1 text-xs text-blue-500">
          Net: {totalAdj >= 0 ? '+' : ''}{fmt(totalAdj)} ({totalAdj >= 0 ? '+' : ''}{totalPct}%)
        </div>
        <div className="text-base font-bold text-blue-700 w-28 text-right">{fmt(fair)}</div>
      </div>
    </div>
  )
}
