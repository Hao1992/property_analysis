import type { SafetyData } from '../types/analysis'
import SourceBadge from './SourceBadge'
import { useLanguage } from '../contexts/LanguageContext'

interface Props { safety: SafetyData }

const barColor = (v: number) =>
  v >= 70 ? 'bg-green-500' : v >= 50 ? 'bg-amber-500' : 'bg-red-500'

const INDICES = [
  'theft_rate_index',
  'vehicle_crime_index',
  'vandalism_index',
  'night_safety_index',
] as const

export default function SafetyModule({ safety }: Props) {
  const { t } = useLanguage()

  const label = (v: number) =>
    v >= 70 ? t.sections.safety.levels.safe : v >= 50 ? t.sections.safety.levels.moderate : t.sections.safety.levels.elevated

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{t.sections.safety.label}</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{t.sections.safety.title} — {safety.district}</h3>
        </div>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{safety.data_year} {t.sections.safety.year}</span>
      </div>

      <div className="space-y-4">
        {INDICES.map((key) => {
          const val = safety[key]
          const lbl = t.sections.safety.indices[key]
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
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{t.sections.safety.note}</p>
        <SourceBadge sources={[{ label: 'Open Data Barcelona — Seguretat Ciutadana', url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/estadistica-de-seguretat-ciutadana', note: `${safety.data_year} data` }]} />
      </div>
    </div>
  )
}
