import { useState } from 'react'
import type { CompositeScore, DimensionScore } from '../types/analysis'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { useLanguage } from '../contexts/LanguageContext'

interface Props { score: CompositeScore }

const SCORE_TEXT = (s: number) => s >= 75 ? 'text-emerald-600' : s >= 55 ? 'text-amber-600' : 'text-red-600'

// Calibrated on BCN+Madrid combined market distribution
const MARKET_PERCENTILE = (score: number): number => {
  if (score >= 85) return 97; if (score >= 80) return 93; if (score >= 75) return 87
  if (score >= 70) return 78; if (score >= 65) return 66; if (score >= 60) return 54
  if (score >= 55) return 42; if (score >= 50) return 30; if (score >= 45) return 20
  if (score >= 40) return 12; return 6
}

function DimPanel({ d, onClose }: { d: DimensionScore; onClose: () => void }) {
  const { t } = useLanguage()
  const sc = t.sections.scoreCard
  const desc = (sc.dimDesc as Record<string, { title: string; what: string }>)[d.name]
  const subEntries = Object.entries(d.sub_scores ?? {})
    .filter(([, v]) => v !== null && v !== undefined)
    .sort(([, a], [, b]) => (b as number) - (a as number))

  return (
    <div className="col-span-4 sm:col-span-8 card p-4 text-xs space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-sm" style={{ color: 'var(--text-main)' }}>{desc?.title ?? d.name}</p>
          <p className="mt-0.5 leading-relaxed" style={{ color: 'var(--text-sub)' }}>{desc?.what}</p>
        </div>
        <button onClick={onClose} className="shrink-0 text-lg leading-none hover:opacity-60" style={{ color: 'var(--text-muted)' }}>×</button>
      </div>
      {subEntries.length > 0 && (
        <div className="space-y-2">
          {subEntries.map(([k, v]) => {
            const val = v as number
            const bar = val >= 70 ? 'bg-emerald-500' : val >= 45 ? 'bg-amber-500' : 'bg-red-500'
            const txt = val >= 70 ? 'text-emerald-600' : val >= 45 ? 'text-amber-600' : 'text-red-600'
            return (
              <div key={k}>
                <div className="flex justify-between mb-1">
                  <span className="capitalize" style={{ color: 'var(--text-sub)' }}>{k.replace(/_/g, ' ')}</span>
                  <span className={`font-semibold ${txt}`}>{Math.round(val)}</span>
                </div>
                <div className="w-full bg-stone-100 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full ${bar}`} style={{ width: `${val}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      )}
      <p style={{ color: 'var(--text-muted)' }}>
        {sc.countsFor(parseFloat((d.weight * 100).toFixed(0)))}
      </p>
    </div>
  )
}

export default function ScoreCard({ score }: Props) {
  const { t } = useLanguage()
  const sc = t.sections.scoreCard
  const [openDim, setOpenDim] = useState<string | null>(null)

  const dimShort = sc.dimShort as Record<string, string>
  const radarData = score.dimensions.map(d => ({ subject: dimShort[d.name] ?? d.name, score: d.score, fullMark: 100 }))
  const confPct      = Math.round((score.confidence ?? 1) * 100)
  const missingDims  = score.dimensions.filter(d => d.score === null || d.score === undefined)
  const percentile   = MARKET_PERCENTILE(score.composite)
  const confStyle    = confPct >= 80 ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : confPct >= 60 ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-red-50 border-red-200 text-red-700'

  const penalties = t.sections.score.penalties as Record<string, string>

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4 gap-4">
        <div className="flex-1">
          <p className="text-xs font-medium uppercase tracking-widest mb-2" style={{ color: 'var(--accent)' }}>{t.sections.score.label}</p>
          <div className="flex items-baseline gap-2">
            <span className="score-number text-6xl font-bold">{score.composite}</span>
            <span className="text-xl" style={{ color: 'var(--text-muted)' }}>/100</span>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-stone-100">
              <div className="h-full rounded-full" style={{ width: `${percentile}%`, backgroundColor: 'var(--accent)' }} />
            </div>
            <span className="text-xs shrink-0" style={{ color: 'var(--text-muted)' }}>
              {t.sections.score.better} <span className="font-semibold" style={{ color: 'var(--text-main)' }}>{percentile}</span>{t.sections.score.ofBCN}
            </span>
          </div>
        </div>

        <div className="w-48 h-48">
          <ResponsiveContainer>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#E8E0D5" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#A8A29E' }} />
              <Radar dataKey="score" stroke="#C67C3A" fill="#C67C3A" fillOpacity={0.15} />
              <Tooltip
                contentStyle={{ background: '#fff', border: '1px solid #E8E0D5', borderRadius: 8, fontSize: 12 }}
                formatter={(v: number) => [v, 'Score']}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {confPct < 90 && (
        <div className={`mb-4 flex items-start gap-2 border rounded-lg px-3 py-2 text-xs ${confStyle}`}>
          <span className="font-semibold shrink-0">{t.sections.score.confidence(confPct)}</span>
          <span className="leading-relaxed">
            {t.sections.score.confidenceSub(confPct)}
            {missingDims.length > 0 && ` ${t.sections.score.missing} ${missingDims.map(d => (sc.dimDesc as Record<string, { title: string }>)[d.name]?.title ?? d.name).join(', ')}.`}
            {' '}{t.sections.score.addDetails}
          </span>
        </div>
      )}

      <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
        {score.dimensions.map(d => {
          const isOpen   = openDim === d.name
          const hasScore = d.score != null
          return (
            <button
              key={d.name}
              onClick={() => setOpenDim(isOpen ? null : d.name)}
              className={`text-center rounded-xl py-2.5 px-1 transition-all border cursor-pointer
                ${isOpen ? 'border-2 shadow-sm' : hasScore ? 'hover:shadow-sm' : 'border-dashed'}`}
              style={{
                borderColor: isOpen ? 'var(--accent)' : hasScore ? 'var(--border)' : '#D6D3D1',
                backgroundColor: isOpen ? '#FEF9F5' : hasScore ? '#fff' : '#FAFAF8',
              }}
            >
              <div className={`text-xl font-bold ${hasScore ? SCORE_TEXT(d.score as number) : 'text-stone-300'}`}>
                {hasScore ? Math.round(d.score as number) : '—'}
              </div>
              <div className="text-xs mt-0.5 leading-tight" style={{ color: 'var(--text-muted)' }}>{dimShort[d.name] ?? d.name}</div>
            </button>
          )
        })}

        {openDim && (() => {
          const dim = score.dimensions.find(d => d.name === openDim)
          return dim ? <DimPanel d={dim} onClose={() => setOpenDim(null)} /> : null
        })()}
      </div>

      {Object.entries(score.penalty_multipliers).some(([, v]) => v !== 1) && (
        <div className="mt-4 pt-4 border-t space-y-1.5" style={{ borderColor: 'var(--border)' }}>
          <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>{t.sections.score.adjustments}</p>
          {Object.entries(score.penalty_multipliers)
            .filter(([, v]) => v !== 1)
            .map(([key, val]) => {
              const pre   = score.composite_pre_penalty
              const pts   = Math.round(pre * (val - 1))
              const pct   = Math.round(Math.abs(1 - val) * 100)
              const isBon = val > 1
              const labelKey = key === 'tourist_saturation'
                ? (isBon ? 'tourist_saturation_bonus' : 'tourist_saturation_penalty')
                : key
              const label = penalties[labelKey] ?? key.replace(/_/g, ' ')
              return (
                <div key={key} className={`flex items-center justify-between rounded-lg px-3 py-2 text-xs border
                  ${isBon ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
                  <span className={isBon ? 'text-emerald-700' : 'text-red-700'}>{label}</span>
                  <span className={`font-semibold ml-3 shrink-0 ${isBon ? 'text-emerald-600' : 'text-red-600'}`}>
                    {isBon ? '+' : ''}{pts} pts ({isBon ? '+' : '-'}{pct}%)
                  </span>
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}
