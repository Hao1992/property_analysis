import type { SafetyData } from '../types/analysis'
import SourceBadge from './SourceBadge'
import ConfidenceBadge from './ConfidenceBadge'
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
  const { t, lang } = useLanguage()

  const label = (v: number) =>
    v >= 70 ? t.sections.safety.levels.safe : v >= 50 ? t.sections.safety.levels.moderate : t.sections.safety.levels.elevated

  const hasData = safety.theft_rate_index != null

  if (!hasData) {
    return (
      <div className="card p-5 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{t.sections.safety.label}</p>
            <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{t.sections.safety.title}</h3>
          </div>
          <ConfidenceBadge level="district" />
        </div>
        <div className="bg-stone-50 border border-stone-200 rounded-lg px-4 py-5 text-center">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {lang === 'zh'
              ? '安全数据暂时仅支持巴塞罗那（来源：Open Data Barcelona）。马德里安全数据将在后续版本中添加。'
              : 'Crime index data is currently available for Barcelona only (Open Data BCN). Madrid safety data will be added in a future update.'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{t.sections.safety.label}</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{t.sections.safety.title}{safety.district ? ` — ${safety.district}` : ''}</h3>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {safety.data_year && <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{safety.data_year} {t.sections.safety.year}</span>}
          <ConfidenceBadge level="district" />
        </div>
      </div>

      <div className="space-y-4">
        {INDICES.map((key) => {
          const val = safety[key]
          if (val == null) return null
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

      {/* District-level data warning — prominently shown per Reddit feedback */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800">
        {t.sections.safety.districtWarning}
      </div>

      <SourceBadge sources={[{ label: 'Open Data Barcelona — Seguretat Ciutadana', url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/estadistica-de-seguretat-ciutadana', note: `${safety.data_year} data` }]} />
    </div>
  )
}
