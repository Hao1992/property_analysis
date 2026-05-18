import { HiddenCostsData } from '../types/analysis';
import SourceBadge from './SourceBadge';

interface Props {
  data: HiddenCostsData;
}

const DERRAMA_COLOR: Record<string, string> = {
  low:    'text-emerald-400',
  medium: 'text-amber-400',
  high:   'text-red-400',
};

function Row({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
      <div>
        <p className="text-sm text-slate-300">{label}</p>
        {sub && <p className="text-xs text-slate-500">{sub}</p>}
      </div>
      <p className="text-sm font-medium text-white">{value}</p>
    </div>
  );
}

export default function HiddenCostBreakdown({ data }: Props) {
  const fmt = (n: number) => `€${n.toLocaleString('es-ES')}`;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Hidden Costs</h3>
        <div className="text-right">
          <p className="text-xs text-slate-400">Total monthly (excl. mortgage)</p>
          <p className="text-xl font-bold text-white">{fmt(data.total_monthly_eur)}<span className="text-sm font-normal text-slate-400">/mo</span></p>
        </div>
      </div>

      <div>
        <Row label="IBI (annual property tax)" value={`${fmt(data.ibi_annual_eur)}/yr`} />
        <Row label="Community fee" value={`${fmt(data.community_fee_monthly_eur)}/mo`} sub="Building maintenance, shared spaces" />
        <Row label="Estimated utilities" value={`${fmt(data.utility_estimate_monthly_eur)}/mo`} sub="Electricity, water, gas" />
        <Row
          label="Derrama provision"
          value={`${fmt(data.derrama_provision_monthly_eur)}/mo`}
          sub={`Risk: ${data.derrama_risk_label.toUpperCase()}`}
        />
      </div>

      {/* Derrama risk warning */}
      {data.derrama_risk_label !== 'low' && (
        <div className={`text-xs rounded-lg px-3 py-2 ${data.derrama_risk_label === 'high' ? 'bg-red-900/30 border border-red-800' : 'bg-amber-900/30 border border-amber-800'}`}>
          <span className={`font-semibold ${DERRAMA_COLOR[data.derrama_risk_label]}`}>
            {data.derrama_risk_label === 'high' ? '⚠ High derrama risk:' : 'Moderate derrama risk:'}
          </span>
          {' '}Building age and ITE status suggest possible unexpected major repair levies. Request community meeting minutes and reserve fund balance before signing.
        </div>
      )}

      {/* Energy upgrade */}
      {data.energy_upgrade_required && (
        <div className="bg-orange-900/30 border border-orange-800 rounded-lg px-3 py-2 text-xs">
          <span className="font-semibold text-orange-400">2033 energy mandate:</span>
          {' '}This property requires energy efficiency upgrades.
          {data.energy_upgrade_estimate_eur && (
            <> Estimated cost: <span className="font-medium text-white">{fmt(data.energy_upgrade_estimate_eur)}</span>.</>
          )}
        </div>
      )}
      <SourceBadge className="mt-2" sources={[
        { label: 'Catastro', url: 'https://www.catastro.meh.es/', note: 'IBI = cadastral value × 0.75%' },
        { label: 'BCN Open Data', url: 'https://opendata-ajuntament.barcelona.cat/', note: 'avg community fee by building age' },
      ]} />
    </div>
  );
}
