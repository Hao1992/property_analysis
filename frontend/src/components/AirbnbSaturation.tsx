import { AirbnbSaturationData } from '../types/analysis';

interface Props {
  data: AirbnbSaturationData;
}

const RISK_CONFIG = {
  low:       { label: 'Low', color: 'text-emerald-400', bar: 'bg-emerald-500', pct: 15 },
  medium:    { label: 'Medium', color: 'text-amber-400', bar: 'bg-amber-500', pct: 45 },
  high:      { label: 'High', color: 'text-orange-400', bar: 'bg-orange-500', pct: 72 },
  very_high: { label: 'Very High', color: 'text-red-400', bar: 'bg-red-500', pct: 95 },
};

export default function AirbnbSaturation({ data }: Props) {
  const cfg = RISK_CONFIG[data.risk_label] ?? RISK_CONFIG.medium;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Tourist Apartment Pressure</h3>
        <span className={`text-sm font-bold ${cfg.color}`}>{cfg.label}</span>
      </div>

      {/* Bar gauge */}
      <div className="w-full bg-slate-700 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all ${cfg.bar}`}
          style={{ width: `${cfg.pct}%` }}
        />
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-bold text-white">
            {data.tourist_pct_building != null ? `${data.tourist_pct_building}%` : '—'}
          </p>
          <p className="text-xs text-slate-400">Est. same building</p>
        </div>
        <div>
          <p className="text-lg font-bold text-white">{data.tourist_count_100m}</p>
          <p className="text-xs text-slate-400">Within 100m</p>
        </div>
        <div>
          <p className="text-lg font-bold text-white">{data.tourist_count_500m}</p>
          <p className="text-xs text-slate-400">Within 500m</p>
        </div>
      </div>

      {data.risk_label === 'very_high' && (
        <p className="text-xs text-red-400 bg-red-900/30 border border-red-800 rounded-lg px-3 py-2">
          Very high tourist apartment density can affect community life, noise levels, building maintenance costs, and community meeting quorum.
        </p>
      )}
      {data.risk_label === 'high' && (
        <p className="text-xs text-orange-400 bg-orange-900/30 border border-orange-800 rounded-lg px-3 py-2">
          Significant tourist apartment presence in this area. Ask the community administrator for the exact count in your building.
        </p>
      )}

      <p className="text-xs text-slate-500">Source: {data.data_source}</p>
    </div>
  );
}
