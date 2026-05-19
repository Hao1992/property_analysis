import { HiddenCostsData } from '../types/analysis';
import SourceBadge from './SourceBadge';
import { useLanguage } from '../contexts/LanguageContext';

interface Props { data: HiddenCostsData; }

function Row({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
      <div>
        <p className="text-sm" style={{ color: 'var(--text-main)' }}>{label}</p>
        {sub && <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{sub}</p>}
      </div>
      <p className="text-sm font-semibold" style={{ color: 'var(--text-main)' }}>{value}</p>
    </div>
  );
}

export default function HiddenCostBreakdown({ data }: Props) {
  const { t } = useLanguage()
  const costs = t.sections.costs
  const fmt = (n: number) => `€${n.toLocaleString('es-ES')}`;

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{costs.label}</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{costs.title}</h3>
        </div>
        <div className="text-right">
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{costs.totalLabel}</p>
          <p className="font-display text-2xl font-bold" style={{ color: 'var(--text-main)' }}>
            {fmt(data.total_monthly_eur)}<span className="text-base font-normal" style={{ color: 'var(--text-muted)' }}>/mo</span>
          </p>
        </div>
      </div>

      <div>
        <Row label={costs.rows.ibi}       value={`${fmt(data.ibi_annual_eur)}/yr`} />
        <Row label={costs.rows.community} value={`${fmt(data.community_fee_monthly_eur)}/mo`} sub={costs.rows.communitySub} />
        <Row label={costs.rows.utilities} value={`${fmt(data.utility_estimate_monthly_eur)}/mo`} sub={costs.rows.utilitiesSub} />
        <Row
          label={costs.rows.derrama}
          value={`${fmt(data.derrama_provision_monthly_eur)}/mo`}
          sub={`${costs.rows.derramaRisk} ${data.derrama_risk_label.toUpperCase()}`}
        />
      </div>

      {data.derrama_risk_label !== 'low' && (
        <div className={`text-xs rounded-lg px-3 py-2 border ${
          data.derrama_risk_label === 'high' ? 'bg-red-50 border-red-200 text-red-700' : 'bg-amber-50 border-amber-200 text-amber-700'
        }`}>
          <span className="font-semibold">{data.derrama_risk_label === 'high' ? costs.derrama.high : costs.derrama.medium}</span>
          {' '}{costs.derrama.text}
        </div>
      )}

      {data.energy_upgrade_required && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-xs text-orange-700">
          <span className="font-semibold">{costs.energyMandate}</span>
          {' '}{costs.energyText}
          {data.energy_upgrade_estimate_eur && (
            <> {costs.energyCost} <span className="font-semibold">€{data.energy_upgrade_estimate_eur.toLocaleString()}</span>.</>
          )}
        </div>
      )}

      <SourceBadge className="mt-2" sources={[
        { label: 'Catastro', url: 'https://www.catastro.meh.es/', note: 'IBI = cadastral × 0.75%' },
        { label: 'BCN Open Data', url: 'https://opendata-ajuntament.barcelona.cat/', note: 'avg community fee by building age' },
      ]} />
    </div>
  );
}
