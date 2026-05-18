import type { SafetyData } from '../types/analysis'
import SourceBadge from './SourceBadge'

interface Props { safety: SafetyData }

const barColor = (v: number) =>
  v >= 70 ? 'bg-green-500' : v >= 50 ? 'bg-amber-500' : 'bg-red-500'

const label = (v: number) =>
  v >= 70 ? 'Safe' : v >= 50 ? 'Moderate' : 'Elevated risk'

const INDICES = [
  { key: 'theft_rate_index',    label: 'Theft rate' },
  { key: 'vehicle_crime_index', label: 'Vehicle crime' },
  { key: 'vandalism_index',     label: 'Vandalism' },
  { key: 'night_safety_index',  label: 'Night safety' },
] as const

export default function SafetyModule({ safety }: Props) {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>District Safety</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>Safety — {safety.district}</h3>
        </div>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{safety.data_year} data</span>
      </div>

      <div className="space-y-4">
        {INDICES.map(({ key, label: lbl }) => {
          const val = safety[key]
          const textCls = val >= 70 ? 'text-emerald-600' : val >= 50 ? 'text-amber-600' : 'text-red-600'
          return (
            <div key={key}>
              <div className="flex justify-between text-sm mb-1">
                <span style={{ color: 'var(--text-sub)' }}>{lbl}</span>
                <span className={`font-medium ${textCls}`}>{val} — {label(val)}</span>
              </div>
              <div className="w-full bg-stone-100 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${barColor(val)}`}
                  style={{ width: `${val}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="space-y-1">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>All indices 0–100 (100 = safest). District-level data, not street-level.</p>
        <SourceBadge sources={[{ label: 'Open Data Barcelona — Seguretat Ciutadana', url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/estadistica-de-seguretat-ciutadana', note: `${safety.data_year} data` }]} />
      </div>
    </div>
  )
}
