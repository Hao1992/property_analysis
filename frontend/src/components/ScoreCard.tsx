import { useState } from 'react'
import type { CompositeScore, DimensionScore } from '../types/analysis'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip
} from 'recharts'

interface Props { score: CompositeScore }

const SCORE_COLOR = (s: number) =>
  s >= 75 ? 'text-emerald-400' : s >= 55 ? 'text-amber-400' : 'text-red-400'

// Approximate Barcelona composite score distribution (editorial estimate based on
// typical BCN property quality: noise, tourist pressure, building age, pricing).
// Maps score → estimated percentile (what % of BCN properties score BELOW this).
const BCN_PERCENTILE = (score: number): number => {
  if (score >= 85) return 97
  if (score >= 80) return 93
  if (score >= 75) return 87
  if (score >= 70) return 78
  if (score >= 65) return 66
  if (score >= 60) return 54
  if (score >= 55) return 42
  if (score >= 50) return 30
  if (score >= 45) return 20
  if (score >= 40) return 12
  return 6
}

const DIM_SHORT: Record<string, string> = {
  Convenience: 'Conv.',
  Safety:      'Safety',
  Property:    'Prop.',
  Market:      'Market',
  Risk:        'Risk',
  Liveability: 'Live.',
  HiddenCosts: 'Costs',
  Intangible:  'Intang.',
}

const DIM_DESC: Record<string, { title: string; what: string }> = {
  Convenience: {
    title: 'Convenience',
    what:  'Metro/bus proximity and frequency, supermarkets, pharmacies, hospitals nearby.',
  },
  Safety: {
    title: 'Safety',
    what:  'District-level crime indices: theft, vehicle crime, vandalism, night safety. Source: BCN Open Data 2024.',
  },
  Property: {
    title: 'Property condition',
    what:  'Building age, era-specific risks (aluminosis, asbestos), orientation, energy certificate. Requires year built data.',
  },
  Market: {
    title: 'Market positioning',
    what:  'How listing price compares to INE median for this census section. Also includes rental yield and market liquidity.',
  },
  Risk: {
    title: 'Risk factors',
    what:  'Structural/material risks, flood/seismic zone, regulatory risk, heritage listing restrictions, rent control status.',
  },
  Liveability: {
    title: 'Liveability',
    what:  'Noise levels (day/night/weekend), school quality, neighbourhood business trajectory.',
  },
  HiddenCosts: {
    title: 'Hidden costs',
    what:  'IBI property tax, community fees, utility estimates, derrama (major repair levy) risk, energy upgrade mandate.',
  },
  Intangible: {
    title: 'Intangible quality',
    what:  'Cultural density (libraries, theatres), traditional markets, local vs chain commerce ratio, green space quality.',
  },
}

function DimPanel({ d, onClose }: { d: DimensionScore; onClose: () => void }) {
  const desc = DIM_DESC[d.name]
  const subEntries = Object.entries(d.sub_scores ?? {})
    .filter(([, v]) => v !== null && v !== undefined)
    .sort(([, a], [, b]) => (b as number) - (a as number))

  return (
    <div className="col-span-4 sm:col-span-7 bg-slate-700 rounded-xl p-4 text-xs space-y-3 border border-slate-600">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-white text-sm">{desc?.title ?? d.name}</p>
          <p className="text-slate-400 mt-0.5 leading-relaxed">{desc?.what}</p>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white shrink-0 text-lg leading-none">×</button>
      </div>
      {subEntries.length > 0 && (
        <div className="space-y-1.5">
          {subEntries.map(([k, v]) => {
            const val = v as number
            const barColor = val >= 70 ? 'bg-emerald-500' : val >= 45 ? 'bg-amber-500' : 'bg-red-500'
            return (
              <div key={k}>
                <div className="flex justify-between mb-0.5">
                  <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                  <span className={`font-semibold ${val >= 70 ? 'text-emerald-400' : val >= 45 ? 'text-amber-400' : 'text-red-400'}`}>{Math.round(val)}</span>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full ${barColor}`} style={{ width: `${val}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      )}
      <p className="text-slate-500">Weight in composite score: {(d.weight * 100).toFixed(0)}%</p>
    </div>
  )
}

export default function ScoreCard({ score }: Props) {
  const [openDim, setOpenDim] = useState<string | null>(null)

  const radarData = score.dimensions.map(d => ({
    subject: DIM_SHORT[d.name] ?? d.name,
    score: d.score,
    fullMark: 100,
  }))

  const confPct = Math.round((score.confidence ?? 1) * 100)
  const confColor = confPct >= 80 ? 'text-emerald-400' : confPct >= 60 ? 'text-amber-400' : 'text-red-400'
  const confBg    = confPct >= 80 ? 'bg-emerald-900/30 border-emerald-800' : confPct >= 60 ? 'bg-amber-900/30 border-amber-800' : 'bg-red-900/30 border-red-800'
  const missingDims = score.dimensions.filter(d => d.score === null || d.score === undefined)
  const percentile = BCN_PERCENTILE(score.composite)

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
          <div className="mt-2 flex items-center gap-1.5">
            <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${SCORE_COLOR(score.composite).replace('text-', 'bg-')}`}
                style={{ width: `${percentile}%` }}
              />
            </div>
            <span className="text-xs text-slate-400 shrink-0">
              better than <span className="text-white font-medium">{percentile}%</span> of BCN properties
            </span>
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

      <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
        {score.dimensions.map(d => {
          const isOpen = openDim === d.name
          return (
            <button
              key={d.name}
              onClick={() => setOpenDim(isOpen ? null : d.name)}
              className={`text-center rounded-xl py-2 px-1 transition-all cursor-pointer ring-0 border
                ${isOpen ? 'ring-2 ring-indigo-500 border-indigo-500 bg-slate-600' : d.score == null ? 'bg-slate-700/20 border-dashed border-slate-600' : 'bg-slate-700/50 border-transparent hover:border-slate-500'}`}
              title={`Click to see ${d.name} breakdown`}
            >
              <div className={`text-xl font-bold ${d.score != null ? SCORE_COLOR(d.score) : 'text-slate-600'}`}>
                {d.score != null ? Math.round(d.score) : '—'}
              </div>
              <div className="text-xs text-slate-400 mt-0.5 leading-tight">{DIM_SHORT[d.name] ?? d.name}</div>
              <div className="text-xs text-slate-500">{(d.weight * 100).toFixed(0)}%</div>
            </button>
          )
        })}

        {/* Expanded panel — always full width below the tiles */}
        {openDim && (() => {
          const dim = score.dimensions.find(d => d.name === openDim)
          return dim ? <DimPanel d={dim} onClose={() => setOpenDim(null)} /> : null
        })()}
      </div>

      {Object.entries(score.penalty_multipliers).some(([, v]) => v !== 1) && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-xs text-slate-500 mb-2">Score adjustments</p>
          <div className="space-y-1.5">
            {Object.entries(score.penalty_multipliers)
              .filter(([, v]) => v !== 1)
              .map(([key, val]) => {
                const pre = score.composite_pre_penalty
                const pts = Math.round(pre * (val - 1))
                const pct = Math.round(Math.abs(1 - val) * 100)
                const isBonus = val > 1
                const label: Record<string, string> = {
                  overpriced:          'Listed above fair value estimate',
                  critical_risk:       'Critical structural or safety risk detected',
                  derrama_risk:        'High risk of upcoming major repair levy',
                  tourist_saturation:  isBonus ? 'High tourist demand (STR premium)' : 'High tourist apartment pressure',
                }
                return (
                  <div key={key} className={`flex items-center justify-between rounded-lg px-3 py-2 text-xs ${isBonus ? 'bg-green-900/30 border border-green-800' : 'bg-red-900/30 border border-red-800'}`}>
                    <span className={isBonus ? 'text-green-300' : 'text-red-300'}>
                      {label[key] ?? key.replace(/_/g, ' ')}
                    </span>
                    <span className={`font-semibold ml-3 shrink-0 ${isBonus ? 'text-green-400' : 'text-red-400'}`}>
                      {isBonus ? '+' : ''}{pts} pts ({isBonus ? '+' : '-'}{pct}%)
                    </span>
                  </div>
                )
              })}
          </div>
        </div>
      )}
    </div>
  )
}
