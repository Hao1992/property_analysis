import { NeighbourhoodTrajectoryData } from '../types/analysis';
import SourceBadge from './SourceBadge';
import ConfidenceBadge from './ConfidenceBadge';
import { useLanguage } from '../contexts/LanguageContext';

interface Props { data: NeighbourhoodTrajectoryData; }

const TREND_STYLE = {
  rising:   { color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
  stable:   { color: 'text-stone-700',   bg: 'bg-stone-50  border-stone-200' },
  declining:{ color: 'text-red-700',     bg: 'bg-red-50    border-red-200' },
};

export default function NeighbourhoodTrajectory({ data }: Props) {
  const { t, lang } = useLanguage()
  const traj = t.sections.trajectory

  const hasData = data.trend != null && data.trend_score != null

  if (!hasData) {
    return (
      <div className="card p-5 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{traj.label}</p>
            <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{traj.title}</h3>
          </div>
          <ConfidenceBadge level="estimated" />
        </div>
        <div className="bg-stone-50 border border-stone-200 rounded-lg px-4 py-5 text-center">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {lang === 'zh'
              ? '街区轨迹数据暂时仅支持巴塞罗那（来源：巴塞罗那营业执照数据）。马德里数据将在后续版本中添加。'
              : 'Neighbourhood trajectory data is currently available for Barcelona only (BCN business licences). Madrid data will be added in a future update.'}
          </p>
        </div>
      </div>
    )
  }

  const trend = data.trend as 'rising' | 'stable' | 'declining'
  const trendData = traj.trends[trend] ?? traj.trends.stable
  const trendStyle = TREND_STYLE[trend] ?? TREND_STYLE.stable

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{traj.label}</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{traj.title}</h3>
        </div>
        <ConfidenceBadge level="verified" />
      </div>

      <div className={`flex items-center gap-3 rounded-xl px-4 py-3 border ${trendStyle.bg}`}>
        <span className={`font-display text-3xl font-bold ${trendStyle.color}`}>{trendData.icon}</span>
        <div>
          <p className={`text-lg font-semibold font-display ${trendStyle.color}`}>{trendData.label}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{traj.score} {data.trend_score != null ? Math.round(data.trend_score) : '—'}/100</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-center">
        <div className="bg-stone-50 rounded-xl py-3 border" style={{ borderColor: 'var(--border)' }}>
          <p className="font-display text-xl font-bold" style={{ color: 'var(--text-main)' }}>{data.new_businesses_12m ?? '—'}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{traj.businesses}</p>
        </div>
        <div className="bg-stone-50 rounded-xl py-3 border" style={{ borderColor: 'var(--border)' }}>
          <p className="font-display text-xl font-bold" style={{ color: 'var(--text-main)' }}>{data.renovation_permits_12m ?? '—'}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{traj.permits}</p>
        </div>
      </div>

      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{traj.note}</p>
      <SourceBadge sources={[
        { label: 'BCN Activitats Comercials', url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/activitats-comercials-icub', note: 'business licence registry' },
        { label: "BCN Llicències d'Obres", url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/llicencies-obres-majors', note: 'major works permits' },
      ]} />
    </div>
  );
}
