import { useState, useEffect, useRef } from 'react'
import { compareProperties } from '../api/client'
import type { CompareResponse, CompareRequest } from '../types/analysis'
import { useLanguage } from '../contexts/LanguageContext'

const RISK_COLORS: Record<string, string> = {
  low:       'text-emerald-600',
  medium:    'text-amber-600',
  high:      'text-orange-600',
  very_high: 'text-red-600',
}

const GRADE_COLORS: Record<string, string> = {
  'Excellent buy':          'text-emerald-600',
  'Good buy':               'text-emerald-600',
  'Proceed with caution':   'text-amber-600',
  'High risk — reconsider': 'text-red-600',
}

// ── Address input with Nominatim autocomplete ─────────────────────────────────
function AddressField({
  value, onChange, placeholder,
}: {
  index?: number
  value: string
  onChange: (v: string) => void
  placeholder: string
}) {
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [show, setShow] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (value.length < 5) { setSuggestions([]); return }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const q = encodeURIComponent(value) // countrycodes=es already limits to Spain
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${q}&format=json&limit=5&addressdetails=1&countrycodes=es`,
          { headers: { 'Accept-Language': 'en' } }
        )
        const data = await res.json()
        const names: string[] = data
          .filter((r: { address?: { road?: string; house_number?: string } }) => r.address?.road && r.address?.house_number)
          .map((r: { display_name?: string }) => r.display_name || '')
          .filter(Boolean)
        setSuggestions(names)
        setShow(names.length > 0)
      } catch { /* silent */ }
    }, 400)
  }, [value])

  const inputCls = "w-full px-4 py-3 bg-stone-50 border rounded-xl text-sm outline-none transition-all focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300"

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={e => { onChange(e.target.value); setShow(true) }}
        onBlur={() => setTimeout(() => setShow(false), 150)}
        onFocus={() => suggestions.length > 0 && setShow(true)}
        placeholder={placeholder}
        className={inputCls}
        style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
        autoComplete="off"
      />
      {show && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white border rounded-xl shadow-xl overflow-hidden" style={{ borderColor: 'var(--border)' }}>
          {suggestions.map((s, i) => (
            <li
              key={i}
              onMouseDown={() => { onChange(s); setSuggestions([]); setShow(false) }}
              className="px-4 py-2.5 text-sm cursor-pointer border-b last:border-0 hover:bg-stone-50 truncate"
              style={{ color: 'var(--text-main)', borderColor: 'var(--border)' }}
              title={s}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Stat row ──────────────────────────────────────────────────────────────────
function Row({ label, value, valueClass = '' }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span className={`text-sm font-semibold ${valueClass}`} style={!valueClass ? { color: 'var(--text-main)' } : undefined}>{value}</span>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Compare() {
  const { t, lang } = useLanguage()
  const profiles = t.form.profiles

  const [addresses, setAddresses] = useState(['', ''])
  const [prices, setPrices]       = useState(['', ''])
  const [profile, setProfile]     = useState('balanced')
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState<CompareResponse | null>(null)
  const [error, setError]         = useState<string | null>(null)
  const [progress, setProgress]   = useState(0)

  const setAddr = (i: number, v: string) => { const a = [...addresses]; a[i] = v; setAddresses(a) }
  const setPrice = (i: number, v: string) => { const p = [...prices]; p[i] = v; setPrices(p) }

  const addProperty = () => {
    if (addresses.length < 3) { setAddresses([...addresses, '']); setPrices([...prices, '']) }
  }

  const removeProperty = (i: number) => {
    setAddresses(addresses.filter((_, idx) => idx !== i))
    setPrices(prices.filter((_, idx) => idx !== i))
  }

  const handleCompare = async () => {
    const filled = addresses.map((a, i) => ({ addr: a.trim(), price: prices[i] })).filter(x => x.addr)
    if (filled.length < 2) { setError(lang === 'zh' ? '请至少输入2个地址' : 'Please enter at least 2 addresses.'); return }
    setError(null)
    setLoading(true)
    setResult(null)
    setProgress(0)
    const ticker = setInterval(() => setProgress(p => p < 85 ? p + Math.random() * 6 : p), 900)
    try {
      const req: CompareRequest = {
        addresses: filled.map(x => x.addr),
        listing_prices: filled.map(x => parseFloat(x.price) || 0).filter(Boolean),
        buyer_profile: profile,
      }
      const data = await compareProperties(req)
      setProgress(100)
      setTimeout(() => { setResult(data); setProgress(0) }, 300)
    } catch (e: unknown) {
      setError((e as Error).message || (lang === 'zh' ? '对比失败，请重试' : 'Compare failed.'))
    } finally {
      clearInterval(ticker)
      setLoading(false)
    }
  }

  const labels = ['A', 'B', 'C']
  const propLabel = (i: number) => lang === 'zh' ? `房产 ${labels[i]}` : `Property ${labels[i]}`
  const addLabel  = lang === 'zh' ? '+ 添加第三套房产' : '+ Add 3rd property'
  const compareLabel = loading ? (lang === 'zh' ? '分析中…' : 'Analysing…') : (lang === 'zh' ? '开始对比' : 'Compare')
  const aiLabel = lang === 'zh' ? 'AI 推荐' : 'AI Recommendation'
  const winnerLabel = lang === 'zh' ? '各维度优胜方：' : 'Winner by dimension:'

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="font-display text-2xl font-bold" style={{ color: 'var(--text-main)' }}>
          {lang === 'zh' ? '房产对比' : 'Compare Properties'}
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
          {lang === 'zh' ? '最多同时对比3套房产，AI给出综合推荐。' : 'Side-by-side AI analysis for up to 3 properties.'}
        </p>
      </div>

      {/* Input form */}
      <div className="card p-5 space-y-4">
        {addresses.map((addr, i) => (
          <div key={i} className="space-y-2">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0" style={{ backgroundColor: 'var(--accent)' }}>
                {labels[i]}
              </div>
              <span className="text-sm font-medium" style={{ color: 'var(--text-sub)' }}>{propLabel(i)}</span>
              {addresses.length > 2 && (
                <button onClick={() => removeProperty(i)} className="ml-auto text-xs hover:text-red-500 transition-colors" style={{ color: 'var(--text-muted)' }}>✕ {lang === 'zh' ? '移除' : 'Remove'}</button>
              )}
            </div>
            <AddressField
              index={i}
              value={addr}
              onChange={v => setAddr(i, v)}
              placeholder={lang === 'zh' ? `例如：Carrer de Mallorca 401, Barcelona 或 Calle Serrano 50, Madrid` : `Property ${labels[i]} address`}
            />
            <input
              type="number"
              placeholder={lang === 'zh' ? '挂牌价格（€）——选填' : 'Listing price (€) — optional'}
              value={prices[i]}
              onChange={e => setPrice(i, e.target.value)}
              className="w-full px-4 py-2.5 bg-stone-50 border rounded-xl text-sm outline-none focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300"
              style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
            />
          </div>
        ))}

        {/* Progress bar */}
        {loading && (
          <div className="h-1 bg-stone-100 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-500" style={{ width: `${progress}%`, backgroundColor: 'var(--accent)' }} />
          </div>
        )}

        <div className="flex items-center gap-3 flex-wrap pt-1">
          {addresses.length < 3 && (
            <button
              onClick={addProperty}
              className="text-sm font-medium px-3 py-1.5 rounded-lg border transition-colors hover:opacity-80"
              style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}
            >
              {addLabel}
            </button>
          )}

          <select
            value={profile}
            onChange={e => setProfile(e.target.value)}
            className="px-3 py-1.5 text-sm rounded-lg border outline-none focus:ring-2 focus:ring-amber-300/50"
            style={{ borderColor: 'var(--border)', color: 'var(--text-main)', backgroundColor: 'var(--bg-card)' }}
          >
            {profiles.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>

          <button
            onClick={handleCompare}
            disabled={loading}
            className="ml-auto px-6 py-2 text-sm font-semibold text-white rounded-xl transition-all disabled:opacity-50 hover:opacity-90"
            style={{ backgroundColor: 'var(--accent)' }}
          >
            {compareLabel}
          </button>
        </div>

        {error && (
          <div className="disclosure-red p-3 text-sm text-red-700">{error}</div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-5">
          {/* AI recommendation */}
          <div className="card p-5 space-y-4" style={{ borderColor: '#E8D5C4' }}>
            <div>
              <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{aiLabel}</p>
              <p className="font-display text-lg font-semibold leading-snug" style={{ color: 'var(--text-main)' }}>
                {result.comparison.recommendation}
              </p>
            </div>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-sub)' }}>
              {result.comparison.summary}
            </p>
            {Object.keys(result.comparison.winner_by_dimension).length > 0 && (
              <div>
                <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{winnerLabel}</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(result.comparison.winner_by_dimension).map(([dim, winner]) => (
                    <span key={dim} className="text-xs px-2.5 py-1 rounded-lg bg-stone-50 border" style={{ borderColor: 'var(--border)' }}>
                      <span style={{ color: 'var(--text-muted)' }}>{dim}:</span>{' '}
                      <span className="font-semibold" style={{ color: 'var(--accent)' }}>{winner as string}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Side-by-side property cards */}
          <div className={`grid gap-4 ${result.analyses.length === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-3'}`}>
            {result.analyses.map((a, i) => {
              const gradeText = lang === 'zh'
                ? (t.sections.narrative.grades as Record<string, string>)[a.grade] ?? a.grade
                : a.grade
              const riskText = lang === 'zh'
                ? (t.sections.airbnb.risks as Record<string, string>)[a.airbnb_risk] ?? a.airbnb_risk
                : a.airbnb_risk.replace('_', ' ')

              return (
                <div key={i} className="card p-5 space-y-4">
                  {/* Header */}
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0" style={{ backgroundColor: 'var(--accent)' }}>
                      {labels[i]}
                    </div>
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--text-sub)' }}>{a.address}</p>
                  </div>

                  {/* Score */}
                  <div className="flex items-baseline gap-2">
                    <span className="score-number text-4xl font-bold">{a.composite_score}</span>
                    <span className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>/100</span>
                    <span className={`ml-1 text-sm font-semibold ${GRADE_COLORS[a.grade] ?? ''}`}>{gradeText}</span>
                  </div>

                  {/* Stats */}
                  <div>
                    <Row label={lang === 'zh' ? '公允价值' : 'Fair value'} value={`€${a.fair_value.toLocaleString('es-ES')}`} />
                    {a.vs_listing_pct != null && (
                      <Row
                        label={lang === 'zh' ? '对比挂牌价' : 'vs Listing'}
                        value={`${a.vs_listing_pct > 0 ? '+' : ''}${a.vs_listing_pct.toFixed(1)}%`}
                        valueClass={a.vs_listing_pct > 5 ? 'text-red-600' : a.vs_listing_pct < -5 ? 'text-emerald-600' : ''}
                      />
                    )}
                    <Row label={lang === 'zh' ? '月度隐性费用' : 'Monthly costs'} value={`€${a.hidden_costs_monthly}/mo`} />
                    <Row label={lang === 'zh' ? '治安评分' : 'Safety'} value={`${Math.round(a.safety_score)}/100`} />
                    <Row label={lang === 'zh' ? '学校评分' : 'School'} value={`${Math.round(a.school_score)}/100`} />
                    <Row
                      label={lang === 'zh' ? '旅游公寓风险' : 'Tourist risk'}
                      value={riskText}
                      valueClass={RISK_COLORS[a.airbnb_risk] ?? ''}
                    />
                  </div>

                  {/* Risks */}
                  {a.key_risks.length > 0 && (
                    <div className="bg-red-50 border border-red-100 rounded-xl p-3">
                      <p className="text-xs font-semibold text-red-700 mb-2">
                        {lang === 'zh' ? '主要风险' : 'Key risks'}
                      </p>
                      <ul className="space-y-1.5">
                        {a.key_risks.slice(0, 2).map((r, j) => (
                          <li key={j} className="text-xs text-red-600 flex gap-1.5 leading-snug">
                            <span className="shrink-0 mt-0.5">▲</span>{r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Positives */}
                  {a.key_positives.length > 0 && (
                    <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3">
                      <p className="text-xs font-semibold text-emerald-700 mb-2">
                        {lang === 'zh' ? '主要亮点' : 'Key positives'}
                      </p>
                      <ul className="space-y-1.5">
                        {a.key_positives.slice(0, 2).map((r, j) => (
                          <li key={j} className="text-xs text-emerald-600 flex gap-1.5 leading-snug">
                            <span className="shrink-0 mt-0.5">✓</span>{r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
