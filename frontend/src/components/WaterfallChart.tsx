import type { ValuationAdjustment as Adjustment } from '../types/analysis'
import {
  ComposedChart, Bar, XAxis, YAxis, Tooltip, Cell,
  ResponsiveContainer, ReferenceLine
} from 'recharts'

interface Props {
  base: number
  adjustments: Adjustment[]
  fair: number
}

export default function WaterfallChart({ base, adjustments, fair }: Props) {
  // Build waterfall series: base + each adjustment + fair value bar
  const data: { name: string; value: number; start: number; fill: string }[] = []

  data.push({ name: 'Base', value: base, start: 0, fill: '#94a3b8' })

  let running = base
  for (const adj of adjustments) {
    const impact = adj.impact_eur
    const fill = impact >= 0 ? '#22c55e' : '#ef4444'
    data.push({ name: adj.name, value: Math.abs(impact), start: impact >= 0 ? running : running + impact, fill })
    running += impact
  }

  data.push({ name: 'Fair value', value: fair, start: 0, fill: '#3b82f6' })

  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-3">Adjustment waterfall</h3>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 5, right: 10, left: 60, bottom: 60 }}>
          <XAxis dataKey="name" angle={-35} textAnchor="end" tick={{ fontSize: 10 }} interval={0} />
          <YAxis
            tickFormatter={v => `€${(v / 1000).toFixed(0)}k`}
            tick={{ fontSize: 10 }}
            domain={['auto', 'auto']}
          />
          <Tooltip
            formatter={(v: number, _name: string, props: { payload?: { name: string; fill: string } }) => [
              props.payload?.fill === '#ef4444' ? `-€${v.toLocaleString()}` : `€${v.toLocaleString()}`,
              props.payload?.name ?? ''
            ]}
          />
          <ReferenceLine y={base} stroke="#94a3b8" strokeDasharray="4 2" />
          <Bar dataKey="value" radius={[3, 3, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.fill} />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-400 mt-1 text-center">
        Green = adds value · Red = reduces value · Confidence based on data completeness
      </p>
    </div>
  )
}
