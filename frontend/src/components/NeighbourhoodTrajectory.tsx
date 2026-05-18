import { NeighbourhoodTrajectoryData } from '../types/analysis';
import SourceBadge from './SourceBadge';

interface Props { data: NeighbourhoodTrajectoryData; }

const TREND = {
  rising:   { label: 'Rising',   icon: '↑', color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
  stable:   { label: 'Stable',   icon: '→', color: 'text-stone-700',   bg: 'bg-stone-50  border-stone-200' },
  declining:{ label: 'Declining',icon: '↓', color: 'text-red-700',     bg: 'bg-red-50    border-red-200' },
};

export default function NeighbourhoodTrajectory({ data }: Props) {
  const cfg = TREND[data.trend] ?? TREND.stable;

  return (
    <div className="card p-5 space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>Area Trend</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>Neighbourhood Trajectory</h3>
      </div>

      <div className={`flex items-center gap-3 rounded-xl px-4 py-3 border ${cfg.bg}`}>
        <span className={`font-display text-3xl font-bold ${cfg.color}`}>{cfg.icon}</span>
        <div>
          <p className={`text-lg font-semibold font-display ${cfg.color}`}>{cfg.label}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Trend score: {Math.round(data.trend_score)}/100</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-center">
        <div className="bg-stone-50 rounded-xl py-3 border" style={{ borderColor: 'var(--border)' }}>
          <p className="font-display text-xl font-bold" style={{ color: 'var(--text-main)' }}>{data.new_businesses_12m}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>New businesses (12 mo)</p>
        </div>
        <div className="bg-stone-50 rounded-xl py-3 border" style={{ borderColor: 'var(--border)' }}>
          <p className="font-display text-xl font-bold" style={{ color: 'var(--text-main)' }}>{data.renovation_permits_12m}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Renovation permits (12 mo)</p>
        </div>
      </div>

      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>New BCN activity licences + major works permits in district · higher = more activity</p>
      <SourceBadge sources={[
        { label: 'BCN Activitats Comercials', url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/activitats-comercials-icub', note: 'business licence registry' },
        { label: "BCN Llicències d'Obres", url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/llicencies-obres-majors', note: 'major works permits' },
      ]} />
    </div>
  );
}
