import type { CompositeScore } from '../types/analysis'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip
} from 'recharts'

interface Props { score: CompositeScore }

const SCORE_COLOR = (s: number) =>
  s >= 75 ? 'text-emerald-400' : s >= 55 ? 'text-amber-400' : 'text-red-400'

const DIM_SHORT: Record<string, string> = {
  Convenience: 'Conv.',
  Safety: 'Safety',
  Property: 'Prop.',
  Market: 'Market',
  Risk: 'Risk',
  Liveability: 'Live.',
  HiddenCosts: 'Costs',
}

export default function ScoreCard({ score }: Props) {
  const radarData = score.dimensions.map(d => ({
    subject: DIM_SHORT[d.name] ?? d.name,
    score: d.score,
    fullMark: 100,
  }))

  const confPct = Math.round((score.confidence ?? 1) * 100)
  const confColor = confPct >= 80 ? 'text-emerald-400' : confPct >= 60 ? 'text-amber-400' : 'text-red-400'
  const confBg    = confPct >= 80 ? 'bg-emerald-900/30 border-emerald-800' : confPct >= 60 ? 'bg-amber-900/30 border-amber-800' : 'bg-red-900/30 border-red-800'
  const missingDims = score.dimensions.filter(d => d.score === null || d.score === undefined)

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm text-slate-400 mb-1">Composite score</p>
          <div className="flex items-baseline gap-3">
            <span className={`text-6xl font-bold ${SCORE_COLOR(score.composite)}`}>
              {score.composite}
            </span>
            <span className="text-slate-500 text-xl">/100</span>
          </div>
        </div>

        <div className="w-52 h-52">
          <ResponsiveContainer>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(v: number) => [v, 'Score']}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Confidence badge — show when partial data */}
      {confPct < 90 && (
        <div className={`mb-4 flex items-start gap-2 border rounded-lg px-3 py-2 ${confBg}`}>
          <span className={`text-xs font-semibold ${confColor} shrink-0 mt-0.5`}>
            {confPct}% data
          </span>
          <p className="text-xs text-slate-400 leading-relaxed">
            Score based on {confPct}% of available data points.
            {missingDims.length > 0 && ` Missing: ${missingDims.map(d => d.name).join(', ')}.`}
            {' '}This score may shift as more data is retrieved.
          </p>
        </div>
      )}

      <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
        {score.dimensions.map(d => (
          <div key={d.name} className={`text-center rounded-xl py-2 px-1 ${d.score == null ? 'bg-slate-700/20 border border-dashed border-slate-600' : 'bg-slate-700/50'}`}>
            <div className={`text-xl font-bold ${d.score != null ? SCORE_COLOR(d.score) : 'text-slate-600'}`}>
              {d.score != null ? d.score : '—'}
            </div>
            <div className="text-xs text-slate-400 mt-0.5 leading-tight">{DIM_SHORT[d.name] ?? d.name}</div>
            <div className="text-xs text-slate-500">{(d.weight * 100).toFixed(0)}%</div>
          </div>
        ))}
      </div>

      {Object.entries(score.penalty_multipliers).some(([, v]) => v < 1) && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-xs text-slate-500 mb-2">Penalties applied:</p>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(score.penalty_multipliers)
              .filter(([, v]) => v < 1)
              .map(([key, val]) => (
                <span key={key} className="text-xs bg-red-900/40 text-red-400 border border-red-800 px-2 py-0.5 rounded-full">
                  {key.replace(/_/g, ' ')} ×{val}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
