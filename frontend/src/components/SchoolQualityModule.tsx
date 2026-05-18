import { SchoolQualityData, SchoolEntry, PoiCategory } from '../types/analysis';
import SourceBadge from './SourceBadge';

interface Props {
  data: SchoolQualityData;
  schoolCategory?: PoiCategory;
}

const SCORE_COLOR = (s: number) =>
  s >= 75 ? 'text-emerald-400' : s >= 55 ? 'text-amber-400' : 'text-red-400'

const TYPE_LABEL: Record<string, { label: string; color: string; bg: string }> = {
  public:     { label: 'Public',     color: 'text-emerald-400', bg: 'bg-emerald-900/30 border-emerald-700' },
  concertada: { label: 'Concertada', color: 'text-blue-400',    bg: 'bg-blue-900/30 border-blue-700' },
  private:    { label: 'Private',    color: 'text-purple-400',  bg: 'bg-purple-900/30 border-purple-700' },
}

const LANG_LABEL: Record<string, string> = {
  catalan: '🇪🇸 Catalan',
  spanish: '🇪🇸 Spanish',
  english: '🇬🇧 English',
  mixed:   'Mixed',
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 75 ? 'bg-emerald-500' : score >= 55 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-xs font-semibold w-8 text-right ${SCORE_COLOR(score)}`}>{Math.round(score)}</span>
    </div>
  )
}

function SchoolCard({ school, isNearest }: { school: SchoolEntry; isNearest: boolean }) {
  const typeConf = TYPE_LABEL[school.school_type] ?? TYPE_LABEL.public
  return (
    <div className={`rounded-xl p-3 border ${isNearest ? 'bg-slate-700/60 border-slate-600' : 'bg-slate-800/40 border-slate-700/50'}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-white truncate">{school.name}</p>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            <span className={`text-xs px-1.5 py-0.5 rounded border ${typeConf.bg} ${typeConf.color}`}>
              {typeConf.label}
            </span>
            <span className="text-xs text-slate-500">{LANG_LABEL[school.language] ?? school.language}</span>
            {isNearest && <span className="text-xs text-indigo-400">· nearest</span>}
          </div>
        </div>
        <span className="text-xs text-slate-500 shrink-0">{school.distance_m}m</span>
      </div>
      <ScoreBar score={school.composite_score} />
      <p className="text-xs text-slate-500 mt-1">
        Score: proximity · {school.school_type === 'private' ? 'private funding' : school.school_type === 'concertada' ? 'subsidised' : 'public'} · quality
      </p>
    </div>
  )
}

export default function SchoolQualityModule({ data }: Props) {
  const schools = data.schools ?? []

  // Group by type
  const byType: Record<string, SchoolEntry[]> = {}
  for (const s of schools) {
    if (!byType[s.school_type]) byType[s.school_type] = []
    byType[s.school_type].push(s)
  }

  const typeOrder: Array<'public' | 'concertada' | 'private'> = ['public', 'concertada', 'private']

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Nearby Schools</h3>

      {schools.length === 0 ? (
        <p className="text-xs text-slate-500">No schools found within 500m.</p>
      ) : (
        <div className="space-y-4">
          {typeOrder.map(type => {
            const group = byType[type]
            if (!group?.length) return null
            const conf = TYPE_LABEL[type]
            return (
              <div key={type}>
                <p className={`text-xs font-semibold uppercase tracking-wide mb-2 ${conf.color}`}>
                  {conf.label} schools ({group.length})
                </p>
                <div className="space-y-2">
                  {group.map((s, i) => (
                    <SchoolCard
                      key={i}
                      school={s}
                      isNearest={s.distance_m === schools[0].distance_m}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      <p className="text-xs text-slate-500">
        Score 0–100: distance (40%) · school type/funding (20%) · quality rating (40%)
      </p>
      <SourceBadge sources={[
        { label: 'OpenStreetMap', url: 'https://www.openstreetmap.org/', note: 'school locations & type tags' },
        { label: 'Ministerio de Educación', url: 'https://datos.gob.es/es/catalogo/ea0010587', note: 'public/concertada/private' },
      ]} />
    </div>
  )
}
