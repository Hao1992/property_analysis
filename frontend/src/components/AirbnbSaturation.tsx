import { AirbnbSaturationData } from '../types/analysis';
import SourceBadge from './SourceBadge';
import ConfidenceBadge from './ConfidenceBadge';
import { useLanguage } from '../contexts/LanguageContext';
import type { City } from './CitySelector';

interface Props {
  data: AirbnbSaturationData;
  city: City;
}

const RISK_CONFIG = {
  low:       { color: 'text-emerald-600', bar: 'bg-emerald-500', bg: 'bg-emerald-50  border-emerald-200', pct: 15 },
  medium:    { color: 'text-amber-600',   bar: 'bg-amber-500',   bg: 'bg-amber-50   border-amber-200',   pct: 45 },
  high:      { color: 'text-orange-600',  bar: 'bg-orange-500',  bg: 'bg-orange-50  border-orange-200',  pct: 72 },
  very_high: { color: 'text-red-600',     bar: 'bg-red-500',     bg: 'bg-red-50     border-red-200',     pct: 95 },
};

export default function AirbnbSaturation({ data, city }: Props) {
  const { t, lang } = useLanguage()
  const airbnb = t.sections.airbnb
  const cfg = RISK_CONFIG[data.risk_label] ?? RISK_CONFIG.medium;
  const isDistrictFallback = data.data_source === 'district-heuristic';
  const isMadrid = city === 'madrid';
  const isZh = lang === 'zh';

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{airbnb.label}</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{airbnb.title}</h3>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <ConfidenceBadge level={isDistrictFallback ? 'district' : 'estimated'} />
          <span className={`text-sm font-bold ${cfg.color}`}>{airbnb.risks[data.risk_label]}</span>
        </div>
      </div>

      {/* Gauge */}
      <div className="w-full bg-stone-100 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${cfg.bar}`} style={{ width: `${cfg.pct}%` }} />
      </div>

      {/* Stats grid — hide specific counts when using district fallback */}
      {!isDistrictFallback ? (
        <div className={`grid gap-3 text-center ${isMadrid ? 'grid-cols-4' : 'grid-cols-3'}`}>
          {[
            { val: data.tourist_pct_building != null ? `${data.tourist_pct_building}%` : '—', label: airbnb.stats[0] },
            { val: data.tourist_count_100m ?? '—', label: airbnb.stats[1] },
            { val: data.tourist_count_500m ?? '—', label: airbnb.stats[2] },
          ].map(({ val, label }) => (
            <div key={label} className="bg-stone-50 rounded-xl py-3">
              <p className="text-xl font-bold font-display" style={{ color: 'var(--text-main)' }}>{val}</p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>
            </div>
          ))}
          {/* Madrid-specific: % unlicensed VUTs */}
          {isMadrid && (
            <div className="bg-red-50 rounded-xl py-3 border border-red-200">
              <p className="text-xl font-bold font-display text-red-600">92.5%</p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                {isZh ? '无有效牌照' : 'VUTs unlicensed'}
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800">
          {airbnb.districtFallbackNote}
        </div>
      )}

      {/* City-specific high/very_high warnings */}
      {(data.risk_label === 'very_high' || data.risk_label === 'high') && (
        isMadrid ? (
          <div className="text-xs rounded-lg px-3 py-2 border bg-red-50 border-red-200 space-y-1.5">
            <p>
              <span className="font-semibold text-red-700">Plan RESIDE (Sep 2025):</span>
              {' '}
              {isZh
                ? '住宅混合楼栋禁止开设新VUT许可证。'
                : 'New tourist licenses blocked in residential buildings across most Madrid districts.'}
            </p>
            <p className="text-red-700">
              <span className="font-semibold">LPH 2025:</span>
              {' '}
              {isZh
                ? '短租现在默认【禁止】——需社区3/5表决同意才能开放。约92.5%的在营VUT无有效合法牌照。'
                : 'Tourist lets now require explicit 3/5 community vote to allow. ~92.5% of active VUTs lack a valid license.'}
            </p>
          </div>
        ) : (
          <div className={`text-xs rounded-lg px-3 py-2 border ${cfg.bg}`}>
            <span className={`font-semibold ${cfg.color}`}>
              {data.risk_label === 'very_high' ? airbnb.warningVeryHigh : airbnb.warningHigh}
            </span>
            {' '}
            {data.risk_label === 'very_high' ? airbnb.textVeryHigh : airbnb.textHigh}
          </div>
        )
      )}

      <SourceBadge sources={
        isMadrid
          ? [
              { label: 'Inside Airbnb', url: 'http://insideairbnb.com/madrid/', note: isDistrictFallback ? 'district-level estimate' : 'active listings (Sep 2025)' },
              { label: 'Plan RESIDE', url: 'https://www.madrid.es/portales/munimadrid/es/Inicio/Actualidad/Noticias/El-Ayuntamiento-activa-un-plan-de-accion-para-ordenar-las-viviendas-de-uso-turistico' },
            ]
          : [
              { label: 'Inside Airbnb', url: 'http://insideairbnb.com/barcelona/', note: isDistrictFallback ? 'district-level estimate (live data unavailable)' : 'active listings' },
              { label: 'Barcelona 2028 ban', url: 'https://www.idealista.com/en/news/property-for-rent-in-spain/2025/06/12/848193-goodbye-airbnb-barcelona-sets-2028-deadline-to-phase-out-tourist-apartments' },
            ]
      } />
    </div>
  );
}
