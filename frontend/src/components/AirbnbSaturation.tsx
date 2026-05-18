import { AirbnbSaturationData } from '../types/analysis';
import SourceBadge from './SourceBadge';

interface Props { data: AirbnbSaturationData; }

const RISK_CONFIG = {
  low:       { label: 'Low',       color: 'text-emerald-600', bar: 'bg-emerald-500', bg: 'bg-emerald-50  border-emerald-200', pct: 15 },
  medium:    { label: 'Medium',    color: 'text-amber-600',   bar: 'bg-amber-500',   bg: 'bg-amber-50   border-amber-200',   pct: 45 },
  high:      { label: 'High',      color: 'text-orange-600',  bar: 'bg-orange-500',  bg: 'bg-orange-50  border-orange-200',  pct: 72 },
  very_high: { label: 'Very High', color: 'text-red-600',     bar: 'bg-red-500',     bg: 'bg-red-50     border-red-200',     pct: 95 },
};

export default function AirbnbSaturation({ data }: Props) {
  const cfg = RISK_CONFIG[data.risk_label] ?? RISK_CONFIG.medium;

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>Tourist Pressure</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>Airbnb Saturation</h3>
        </div>
        <span className={`text-sm font-bold ${cfg.color}`}>{cfg.label}</span>
      </div>

      {/* Gauge */}
      <div className="w-full bg-stone-100 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${cfg.bar}`} style={{ width: `${cfg.pct}%` }} />
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { val: data.tourist_pct_building != null ? `${data.tourist_pct_building}%` : '—', label: 'Est. this building' },
          { val: data.tourist_count_100m,  label: 'Within 100m' },
          { val: data.tourist_count_500m,  label: 'Within 500m' },
        ].map(({ val, label }) => (
          <div key={label} className="bg-stone-50 rounded-xl py-3">
            <p className="text-xl font-bold font-display" style={{ color: 'var(--text-main)' }}>{val}</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>
          </div>
        ))}
      </div>

      {(data.risk_label === 'very_high' || data.risk_label === 'high') && (
        <div className={`text-xs rounded-lg px-3 py-2 border ${cfg.bg}`}>
          <span className={`font-semibold ${cfg.color}`}>
            {data.risk_label === 'very_high' ? '⚠ Very high saturation:' : 'Significant saturation:'}
          </span>
          {' '}
          {data.risk_label === 'very_high'
            ? 'Affects community life, noise, building maintenance, and meeting quorum. All tourist apartment licences expire by November 2028.'
            : 'Notable tourist apartment presence. Verify building community rules before signing.'}
        </div>
      )}

      <SourceBadge sources={[
        { label: 'Inside Airbnb', url: 'http://insideairbnb.com/barcelona/', note: 'active listings' },
        { label: 'Barcelona 2028 ban', url: 'https://www.idealista.com/en/news/property-for-rent-in-spain/2025/06/12/848193-goodbye-airbnb-barcelona-sets-2028-deadline-to-phase-out-tourist-apartments' },
      ]} />
    </div>
  );
}
