import { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';

interface CostLine {
  label: string;
  label_zh: string;
  amount: number;
  rate_pct?: number;
  note: string;
  note_zh: string;
}

interface CalcResult {
  purchase_price: number;
  lines: CostLine[];
  subtotal_taxes: number;
  subtotal_services: number;
  total_costs: number;
  total_pct_of_price: number;
  minimum_cash_required: number;
  warnings: string[];
  warnings_zh: string[];
}

const REGIONS = [
  { value: 'catalonia', en: 'Catalonia (ITP 10%)', zh: '加泰罗尼亚（ITP 10%）' },
  { value: 'madrid',    en: 'Madrid (ITP 6%)',      zh: '马德里（ITP 6%）' },
  { value: 'valencia',  en: 'Valencia (ITP 10%)',   zh: '瓦伦西亚（ITP 10%）' },
  { value: 'other',     en: 'Other region (~8%)',   zh: '其他地区（约8%）' },
];

const BUYER_TYPES = [
  { value: 'resident',     en: 'Spanish resident',  zh: '西班牙居民' },
  { value: 'non_resident', en: 'Non-resident',       zh: '非居民' },
];

function fmt(n: number) {
  return '€' + Math.round(n).toLocaleString('es-ES');
}

export default function CostCalculator() {
  const { t, lang } = useLanguage();
  const calc = t.costCalc;
  const isZh = lang === 'zh';

  const [price, setPrice] = useState('');
  const [region, setRegion] = useState('catalonia');
  const [buyerType, setBuyerType] = useState('resident');
  const [isNewBuild, setIsNewBuild] = useState(false);
  const [mortgage, setMortgage] = useState('');
  const [result, setResult] = useState<CalcResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCalc = async () => {
    const p = parseFloat(price.replace(/[^0-9]/g, ''));
    if (!p || p <= 0) { setError(calc.errorPrice); return; }
    setResult(null);
    setError('');
    setLoading(true);
    try {
      const body = {
        purchase_price: p,
        is_new_build: isNewBuild,
        buyer_type: buyerType,
        region,
        mortgage_amount: mortgage ? parseFloat(mortgage.replace(/[^0-9]/g, '')) : null,
        include_lawyer: true,
      };
      const res = await fetch('/cost-calculator', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const inputCls = "w-full px-3 py-2.5 bg-stone-50 border rounded-xl text-sm outline-none focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300";

  return (
    <div className="card p-5 space-y-5">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{calc.label}</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{calc.title}</h3>
        <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{calc.subtitle}</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-sub)' }}>{calc.priceLabel}</label>
          <input
            type="text"
            value={price}
            onChange={e => setPrice(e.target.value)}
            placeholder={calc.pricePlaceholder}
            className={inputCls}
            style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
          />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-sub)' }}>{calc.mortgageLabel}</label>
          <input
            type="text"
            value={mortgage}
            onChange={e => setMortgage(e.target.value)}
            placeholder={calc.mortgagePlaceholder}
            className={inputCls}
            style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
          />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-sub)' }}>{calc.regionLabel}</label>
          <select value={region} onChange={e => setRegion(e.target.value)} className={inputCls} style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}>
            {REGIONS.map(r => <option key={r.value} value={r.value}>{isZh ? r.zh : r.en}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-sub)' }}>{calc.buyerLabel}</label>
          <select value={buyerType} onChange={e => setBuyerType(e.target.value)} className={inputCls} style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}>
            {BUYER_TYPES.map(b => <option key={b.value} value={b.value}>{isZh ? b.zh : b.en}</option>)}
          </select>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setIsNewBuild(v => !v)}
          className={`px-3 py-1.5 text-xs rounded-lg border transition-all font-medium ${isNewBuild ? 'border-amber-400 bg-amber-50 text-amber-700' : 'border-stone-200 bg-white text-stone-500'}`}
        >
          {isZh ? '新建房（IVA税）' : 'New build (VAT applies)'}
        </button>
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

      <button
        onClick={handleCalc}
        disabled={loading}
        className="w-full py-3 text-white font-semibold rounded-xl transition-all text-sm hover:opacity-90 disabled:opacity-50"
        style={{ backgroundColor: 'var(--accent)' }}
      >
        {loading ? (isZh ? '计算中…' : 'Calculating…') : calc.calcButton}
      </button>

      {result && (
        <div className="space-y-4">
          {/* Summary banner */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{calc.totalCosts}</p>
            <p className="text-2xl font-bold font-display text-amber-700">{fmt(result.total_costs)}</p>
            <p className="text-xs text-amber-600 mt-0.5">+{result.total_pct_of_price}% {isZh ? '额外于购房价之上' : 'on top of purchase price'}</p>
          </div>

          <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 flex justify-between items-center">
            <span className="text-sm font-medium text-emerald-800">{calc.totalCashNeeded}</span>
            <span className="text-lg font-bold font-display text-emerald-700">{fmt(result.minimum_cash_required)}</span>
          </div>

          {/* Line items */}
          <div className="space-y-2">
            {result.lines.map((line, i) => (
              <div key={i} className="bg-stone-50 rounded-xl px-4 py-3 border" style={{ borderColor: 'var(--border)' }}>
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0 mr-3">
                    <p className="text-sm font-medium" style={{ color: 'var(--text-main)' }}>
                      {isZh ? line.label_zh : line.label}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                      {isZh ? line.note_zh : line.note}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-bold" style={{ color: 'var(--text-main)' }}>{fmt(line.amount)}</p>
                    {line.rate_pct != null && (
                      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{line.rate_pct.toFixed(1)}%</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Subtotals */}
          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="bg-stone-50 rounded-xl py-3 border" style={{ borderColor: 'var(--border)' }}>
              <p className="text-lg font-bold text-red-600">{fmt(result.subtotal_taxes)}</p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{isZh ? '税款合计' : 'Total taxes'}</p>
            </div>
            <div className="bg-stone-50 rounded-xl py-3 border" style={{ borderColor: 'var(--border)' }}>
              <p className="text-lg font-bold text-blue-600">{fmt(result.subtotal_services)}</p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{isZh ? '服务费合计' : 'Total services'}</p>
            </div>
          </div>

          {/* Warnings */}
          {(isZh ? result.warnings_zh : result.warnings).map((w, i) => (
            <div key={i} className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-xs text-blue-800">
              {w}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
