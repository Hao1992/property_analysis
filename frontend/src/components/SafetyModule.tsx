import type { SafetyData } from '../types/analysis'
import SourceBadge from './SourceBadge'
import ConfidenceBadge from './ConfidenceBadge'
import { useLanguage } from '../contexts/LanguageContext'
import type { City } from './CitySelector'

interface Props { safety: SafetyData; city?: City }

const barColor = (v: number) =>
  v >= 70 ? 'bg-green-500' : v >= 50 ? 'bg-amber-500' : 'bg-red-500'

const INDICES = [
  'theft_rate_index',
  'vehicle_crime_index',
  'vandalism_index',
  'night_safety_index',
] as const

export default function SafetyModule({ safety, city = 'barcelona' }: Props) {
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
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{safety.data_year} {t.sections.safety.year}</span>
          <ConfidenceBadge level="district" />
        </div>
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

      {/* District-level data warning — prominently shown per Reddit feedback */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800">
        {t.sections.safety.districtWarning}
      </div>

      <SourceBadge sources={[city === 'madrid'
        ? { label: 'Ayuntamiento Madrid — Seguridad Ciudadana', url: 'https://datos.madrid.es/portal/site/egob/menuitem.c05c1f754a33a9fbe4b2e4b284f1a5a0/?vgnextoid=baa555ce2d33f210VgnVCM2000001f4a900aRCRD', note: `${safety.data_year} data` }
        : { label: 'Open Data Barcelona — Seguretat Ciutadana', url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/estadistica-de-seguretat-ciutadana', note: `${safety.data_year} data` }
      ]} />
    </div>
  )
}
