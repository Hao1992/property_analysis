import { NoiseData } from '../types/analysis';
import SourceBadge from './SourceBadge';
import { useLanguage } from '../contexts/LanguageContext';

interface Props { data: NoiseData; }

function Bar({ label, score, hint }: { label: string; score: number; hint?: string }) {
  const bar  = score >= 75 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : 'bg-red-500'
  const text = score >= 75 ? 'text-emerald-600' : score >= 50 ? 'text-amber-600' : 'text-red-600'
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span style={{ color: 'var(--text-sub)' }}>{label}</span>
        <span className={`font-semibold ${text}`}>{score}/100</span>
      </div>
      <div className="w-full bg-stone-100 rounded-full h-2">
        <div className={`h-2 rounded-full ${bar}`} style={{ width: `${score}%` }} />
      </div>
      {hint && <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{hint}</p>}
    </div>
  );
}

export default function NoiseEcosystem({ data }: Props) {
  const { t } = useLanguage()
  const noise = t.sections.noise

  return (
    <div className="card p-5 space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{noise.label}</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{noise.title}</h3>
        <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{noise.scale}</p>
      </div>

      {data.floor_boost_applied > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-xs text-blue-700">
          {noise.floorBonus(data.floor_boost_applied)}
          <span className="ml-1 text-blue-500">{noise.floorBonusSub}</span>
        </div>
      )}

      <div className="space-y-4">
        <Bar label={noise.bars.day} score={data.day_noise_score} />
        <Bar
          label={noise.bars.night}
          score={data.night_noise_score}
          hint={
            data.nightclubs_500m > 0
              ? noise.nightclubs(data.nightclubs_500m, data.bars_clubs_500m - data.nightclubs_500m)
              : data.bars_clubs_500m > 0
              ? noise.barsOnly(data.bars_clubs_500m)
              : undefined
          }
        />
        <Bar label={noise.bars.weekend} score={data.weekend_noise_score} />
      </div>

      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        {(noise.construction as Record<string, string>)[data.construction_risk] ?? ''}
        {' · '}{noise.note}
      </p>
      <SourceBadge sources={[{ label: 'OpenStreetMap via Overpass API', url: 'https://overpass-turbo.eu/', note: 'bars, clubs, nightlife POIs' }]} />
    </div>
  );
}
