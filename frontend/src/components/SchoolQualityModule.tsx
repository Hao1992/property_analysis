import { SchoolQualityData } from '../types/analysis';

interface Props {
  data: SchoolQualityData;
}

function ScoreRing({ score }: { score: number }) {
  const color =
    score >= 75 ? 'text-emerald-400' :
    score >= 55 ? 'text-amber-400' :
    'text-red-400';
  return (
    <div className={`text-3xl font-bold ${color}`}>
      {Math.round(score)}
      <span className="text-sm font-normal text-slate-400">/100</span>
    </div>
  );
}

const TYPE_LABELS: Record<string, string> = {
  public:     'Public',
  concertada: 'Concertada',
  private:    'Private',
};

const LANG_LABELS: Record<string, string> = {
  catalan: 'Catalan',
  spanish: 'Spanish',
  english: 'English',
  mixed:   'Mixed',
};

export default function SchoolQualityModule({ data }: Props) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
      <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Nearest School</h3>

      <div className="flex items-center gap-5">
        <ScoreRing score={data.composite_score} />
        <div className="space-y-1 text-sm">
          {data.nearest_school_m != null && (
            <p className="text-slate-300">
              <span className="text-slate-400">Distance: </span>
              {Math.round(data.nearest_school_m)}m
              {data.nearest_school_m <= 400 && <span className="ml-1 text-emerald-400">· Walking distance</span>}
            </p>
          )}
          {data.school_type && (
            <p className="text-slate-300">
              <span className="text-slate-400">Type: </span>
              {TYPE_LABELS[data.school_type] ?? data.school_type}
            </p>
          )}
          {data.language && (
            <p className="text-slate-300">
              <span className="text-slate-400">Language: </span>
              {LANG_LABELS[data.language] ?? data.language}
            </p>
          )}
          {data.google_rating != null && (
            <p className="text-slate-300">
              <span className="text-slate-400">Rating: </span>
              {'★'.repeat(Math.round(data.google_rating))}
              {'☆'.repeat(5 - Math.round(data.google_rating))}
              {' '}{data.google_rating.toFixed(1)}
            </p>
          )}
        </div>
      </div>

      {!data.nearest_school_m && (
        <p className="text-xs text-slate-500">No school found within 500m.</p>
      )}
      <p className="text-xs text-slate-500">Composite: distance (40%) + type (20%) + Google rating (40%)</p>
    </div>
  );
}
