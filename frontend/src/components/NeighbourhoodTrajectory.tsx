import { NeighbourhoodTrajectoryData } from '../types/analysis';

interface Props {
  data: NeighbourhoodTrajectoryData;
}

const TREND_CONFIG = {
  rising:   { label: 'Rising',   icon: '↑', color: 'text-emerald-400', bg: 'bg-emerald-900/30 border-emerald-800' },
  stable:   { label: 'Stable',   icon: '→', color: 'text-slate-300',   bg: 'bg-slate-700/50 border-slate-600' },
  declining: { label: 'Declining', icon: '↓', color: 'text-red-400',    bg: 'bg-red-900/30 border-red-800' },
};

export default function NeighbourhoodTrajectory({ data }: Props) {
  const cfg = TREND_CONFIG[data.trend] ?? TREND_CONFIG.stable;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Neighbourhood Trajectory</h3>

      <div className={`flex items-center gap-3 rounded-xl px-4 py-3 border ${cfg.bg}`}>
        <span className={`text-3xl font-bold ${cfg.color}`}>{cfg.icon}</span>
        <div>
          <p className={`text-lg font-semibold ${cfg.color}`}>{cfg.label}</p>
          <p className="text-xs text-slate-400">Trend score: {Math.round(data.trend_score)}/100</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-center">
        <div className="bg-slate-700/50 rounded-xl py-3">
          <p className="text-xl font-bold text-white">{data.new_businesses_12m}</p>
          <p className="text-xs text-slate-400">New businesses (12 mo)</p>
        </div>
        <div className="bg-slate-700/50 rounded-xl py-3">
          <p className="text-xl font-bold text-white">{data.renovation_permits_12m}</p>
          <p className="text-xs text-slate-400">Renovation permits (12 mo)</p>
        </div>
      </div>

      <p className="text-xs text-slate-500">
        Signal: new BCN activity licences in district · higher = more commercial activity
      </p>
    </div>
  );
}
