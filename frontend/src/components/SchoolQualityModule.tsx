import { SchoolQualityData, SchoolEntry, PoiCategory } from '../types/analysis';
import SourceBadge from './SourceBadge';

interface Props {
  data: SchoolQualityData;
  schoolCategory?: PoiCategory;
}

const SCORE_COLOR = (s: number) =>
  s >= 75 ? 'text-emerald-600' : s >= 55 ? 'text-amber-600' : 'text-red-500'

const TYPE_LABEL: Record<string, { label: string; color: string; bg: string; border: string }> = {
  public:     { label: 'Public',     color: 'text-emerald-700', bg: 'bg-emerald-50',  border: 'border-emerald-200' },
  concertada: { label: 'Concertada', color: 'text-blue-700',    bg: 'bg-blue-50',     border: 'border-blue-200' },
  private:    { label: 'Private',    color: 'text-purple-700',  bg: 'bg-purple-50',   border: 'border-purple-200' },
}

const TYPE_HEADING: Record<string, string> = {
  public:     'text-emerald-600',
  concertada: 'text-blue-600',
  private:    'text-purple-600',
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
      <div className="flex-1 h-1.5 bg-stone-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-xs font-semibold w-8 text-right ${SCORE_COLOR(score)}`}>{Math.round(score)}</span>
    </div>
  )
}

function SchoolCard({ school, isNearest }: { school: SchoolEntry; isNearest: boolean }) {
  const typeConf = TYPE_LABEL[school.school_type] ?? TYPE_LABEL.public
  return (
    <div className={`rounded-xl p-3 border ${typeConf.border} ${isNearest ? typeConf.bg : 'bg-white'}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <p className="text-sm font-medium truncate" style={{ color: 'var(--text-main)' }}>{school.name}</p>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${typeConf.bg} ${typeConf.border} ${typeConf.color}`}>
              {typeConf.label}
            </span>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{LANG_LABEL[school.language] ?? school.language}</span>
            {isNearest && <span className="text-xs font-medium" style={{ color: 'var(--accent)' }}>· nearest</span>}
          </div>
        </div>
        <span className="text-xs shrink-0" style={{ color: 'var(--text-muted)' }}>{school.distance_m}m</span>
      </div>
      <ScoreBar score={school.composite_score} />
      <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
        Score: proximity · {school.school_type === 'private' ? 'private funding' : school.school_type === 'concertada' ? 'subsidised' : 'public'} · quality
      </p>
    </div>
  )
}

export default function SchoolQualityModule({ data }: Props) {
  const schools = data.schools ?? []

  const byType: Record<string, SchoolEntry[]> = {}
  for (const s of schools) {
    if (!byType[s.school_type]) byType[s.school_type] = []
    byType[s.school_type].push(s)
  }

  const typeOrder: Array<'public' | 'concertada' | 'private'> = ['public', 'concertada', 'private']

  return (
    <div className="card p-5 space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>Education</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>Nearby Schools</h3>
      </div>

      {schools.length === 0 ? (
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No schools found within 500m.</p>
      ) : (
        <div className="space-y-4">
          {typeOrder.map(type => {
            const group = byType[type]
            if (!group?.length) return null
            return (
              <div key={type}>
                <p className={`text-xs font-semibold uppercase tracking-wide mb-2 ${TYPE_HEADING[type]}`}>
                  {TYPE_LABEL[type].label} schools ({group.length})
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

      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        Score 0–100: distance (40%) · school type/funding (20%) · quality rating (40%)
      </p>
      <SourceBadge sources={[
        { label: 'OpenStreetMap', url: 'https://www.openstreetmap.org/', note: 'school locations & type tags' },
        { label: 'Ministerio de Educación', url: 'https://datos.gob.es/es/catalogo/ea0010587', note: 'public/concertada/private' },
      ]} />
    </div>
  )
}
