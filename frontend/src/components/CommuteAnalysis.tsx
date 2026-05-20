import { useState, useRef } from 'react';
import { useLanguage } from '../contexts/LanguageContext';

interface CommuteMode {
  mode: string;
  mode_zh: string;
  duration_minutes: number | null;
  distance_km: number | null;
  note: string;
  note_zh: string;
  quality: string;
}

interface CommuteResult {
  work_address: string;
  modes: CommuteMode[];
  recommendation: string;
  recommendation_zh: string;
}

interface Props {
  homeLat: number;
  homeLng: number;
}

const MODE_ICONS: Record<string, string> = {
  'Walking':         '🚶',
  'Bike / Bicing':   '🚲',
  'Metro (estimated)': '🚇',
  'Car (off-peak)':  '🚗',
};

const QUALITY_CONFIG = {
  great:   { bar: 'bg-emerald-500', text: 'text-emerald-600' },
  ok:      { bar: 'bg-amber-500',   text: 'text-amber-600' },
  long:    { bar: 'bg-red-500',     text: 'text-red-600' },
  unknown: { bar: 'bg-stone-300',   text: 'text-stone-500' },
};

function NominatimSuggest({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string, lat?: number, lng?: number) => void;
  placeholder: string;
}) {
  const [suggestions, setSuggestions] = useState<{ label: string; lat: number; lng: number }[]>([]);
  const [show, setShow] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleInput = (v: string) => {
    onChange(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      if (v.length < 5) { setSuggestions([]); return; }
      try {
        const q = encodeURIComponent(v + (v.toLowerCase().includes('barcelona') ? '' : ', Barcelona'));
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${q}&format=json&limit=4&addressdetails=1&countrycodes=es`,
          { headers: { 'Accept-Language': 'en' } }
        );
        const data = await res.json();
        setSuggestions(
          data
            .filter((r: { display_name?: string }) => r.display_name)
            .map((r: { display_name: string; lat: string; lon: string }) => ({
              label: r.display_name,
              lat: parseFloat(r.lat),
              lng: parseFloat(r.lon),
            }))
        );
        setShow(true);
      } catch { /* silent */ }
    }, 400);
  };

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={e => handleInput(e.target.value)}
        onBlur={() => setTimeout(() => setShow(false), 150)}
        onFocus={() => suggestions.length > 0 && setShow(true)}
        placeholder={placeholder}
        className="w-full px-3 py-2.5 bg-stone-50 border rounded-xl text-sm outline-none focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300"
        style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
        autoComplete="off"
      />
      {show && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white border rounded-xl shadow-xl overflow-hidden" style={{ borderColor: 'var(--border)' }}>
          {suggestions.map((s, i) => (
            <li
              key={i}
              onMouseDown={() => {
                onChange(s.label, s.lat, s.lng);
                setSuggestions([]);
                setShow(false);
              }}
              className="px-4 py-2.5 text-xs cursor-pointer border-b last:border-0 hover:bg-stone-50 truncate"
              style={{ color: 'var(--text-main)', borderColor: 'var(--border)' }}
              title={s.label}
            >
              {s.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function CommuteAnalysis({ homeLat, homeLng }: Props) {
  const { t, lang } = useLanguage();
  const isZh = lang === 'zh';
  const commute = t.commute;

  const [workAddress, setWorkAddress] = useState('');
  const [workLat, setWorkLat] = useState<number | null>(null);
  const [workLng, setWorkLng] = useState<number | null>(null);
  const [result, setResult] = useState<CommuteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCalc = async () => {
    if (workLat === null || workLng === null) { setError(commute.errorWork); return; }
    setResult(null);
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/commute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          home_lat: homeLat, home_lng: homeLng,
          work_lat: workLat, work_lng: workLng,
          work_address: workAddress,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-5 space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{commute.label}</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{commute.title}</h3>
        <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{commute.subtitle}</p>
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-medium" style={{ color: 'var(--text-sub)' }}>{commute.workLabel}</label>
        <NominatimSuggest
          value={workAddress}
          onChange={(v, lat, lng) => {
            setWorkAddress(v);
            if (lat !== undefined) setWorkLat(lat);
            if (lng !== undefined) setWorkLng(lng);
          }}
          placeholder={commute.workPlaceholder}
        />
        {workAddress && !workLat && (
          <p className="text-xs text-amber-700">{commute.selectFromList}</p>
        )}
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

      <button
        onClick={handleCalc}
        disabled={loading || workLat === null}
        className="w-full py-2.5 text-white font-semibold rounded-xl transition-all text-sm hover:opacity-90 disabled:opacity-40"
        style={{ backgroundColor: 'var(--accent)' }}
      >
        {loading ? (isZh ? '计算中…' : 'Calculating…') : commute.calcButton}
      </button>

      {result && (
        <div className="space-y-3">
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-xs text-blue-800">
            {isZh ? result.recommendation_zh : result.recommendation}
          </div>

          <div className="space-y-2">
            {result.modes.map((m) => {
              const icon = Object.entries(MODE_ICONS).find(([k]) => m.mode.startsWith(k))?.[1] ?? '🚌';
              const qcfg = QUALITY_CONFIG[m.quality as keyof typeof QUALITY_CONFIG] ?? QUALITY_CONFIG.unknown;
              const pct = m.duration_minutes ? Math.min(100, m.duration_minutes / 60 * 100) : 0;
              return (
                <div key={m.mode} className="bg-stone-50 rounded-xl px-4 py-3 border" style={{ borderColor: 'var(--border)' }}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium flex items-center gap-1.5" style={{ color: 'var(--text-main)' }}>
                      <span>{icon}</span>
                      {isZh ? m.mode_zh : m.mode}
                    </span>
                    <span className={`text-sm font-bold ${qcfg.text}`}>
                      {m.duration_minutes != null ? `${m.duration_minutes} min` : '—'}
                    </span>
                  </div>
                  <div className="w-full bg-stone-200 rounded-full h-1.5 mb-1.5">
                    <div className={`h-1.5 rounded-full ${qcfg.bar}`} style={{ width: `${pct}%` }} />
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{isZh ? m.note_zh : m.note}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
