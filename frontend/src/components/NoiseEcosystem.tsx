import { NoiseData } from '../types/analysis';

interface Props {
  data: NoiseData;
}

function Bar({ label, score, hint }: { label: string; score: number; hint?: string }) {
  const color =
    score >= 75 ? 'bg-emerald-500' :
    score >= 50 ? 'bg-amber-500' :
    'bg-red-500';
  const textColor =
    score >= 75 ? 'text-emerald-400' :
    score >= 50 ? 'text-amber-400' :
    'text-red-400';

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-300">{label}</span>
        <span className={`font-semibold ${textColor}`}>{score}/100</span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

const CONSTRUCTION_LABELS: Record<string, string> = {
  low:    'Low construction activity nearby',
  medium: 'Some renovation activity expected',
  high:   'High renovation activity (old building area)',
};

export default function NoiseEcosystem({ data }: Props) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Noise Ecosystem</h3>
      <p className="text-xs text-slate-400">100 = very quiet · lower = noisier</p>

      {data.floor_boost_applied > 0 && (
        <div className="bg-indigo-900/30 border border-indigo-800 rounded-lg px-3 py-2 text-xs text-indigo-300">
          Floor level bonus applied: +{data.floor_boost_applied} pts
          <span className="text-slate-400 ml-1">(higher floors receive less street noise)</span>
        </div>
      )}

      <div className="space-y-4">
        <Bar label="Daytime" score={data.day_noise_score} />
        <Bar
          label="Night (bars &amp; nightlife)"
          score={data.night_noise_score}
          hint={
            data.nightclubs_500m > 0
              ? `${data.nightclubs_500m} nightclub(s) + ${data.bars_clubs_500m - data.nightclubs_500m} bar(s) within 500m`
              : data.bars_clubs_500m > 0
              ? `${data.bars_clubs_500m} bar/pub venue(s) within 500m — no nightclubs`
              : undefined
          }
        />
        <Bar label="Weekend overall" score={data.weekend_noise_score} />
      </div>

      <p className="text-xs text-slate-500">
        {CONSTRUCTION_LABELS[data.construction_risk] ?? ''}
        {' · Bars also counted as convenience amenities in the Convenience score.'}
      </p>
    </div>
  );
}
