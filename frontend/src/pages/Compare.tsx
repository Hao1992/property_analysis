import { useState } from 'react'
import { compareProperties } from '../api/client'
import type { CompareResponse, CompareRequest } from '../types/analysis'

const PROFILES = [
  { value: 'balanced', label: 'Balanced' },
  { value: 'family', label: 'Family' },
  { value: 'investor', label: 'Investor' },
  { value: 'retiree', label: 'Retiree' },
  { value: 'expat', label: 'Expat' },
]

const RISK_COLORS: Record<string, string> = {
  low:       'text-emerald-400',
  medium:    'text-amber-400',
  high:      'text-orange-400',
  very_high: 'text-red-400',
}

const GRADE_COLORS: Record<string, string> = {
  'Excellent buy':          'text-emerald-400',
  'Good buy':               'text-green-400',
  'Proceed with caution':   'text-amber-400',
  'High risk — reconsider': 'text-red-400',
}

export default function Compare() {
  const [addresses, setAddresses] = useState(['', ''])
  const [prices, setPrices] = useState(['', ''])
  const [profile, setProfile] = useState('balanced')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CompareResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const addAddress = () => {
    if (addresses.length < 3) {
      setAddresses([...addresses, ''])
      setPrices([...prices, ''])
    }
  }

  const removeAddress = (i: number) => {
    setAddresses(addresses.filter((_, idx) => idx !== i))
    setPrices(prices.filter((_, idx) => idx !== i))
  }

  const handleSubmit = async () => {
    const filled = addresses.filter(a => a.trim())
    if (filled.length < 2) { setError('Enter at least 2 addresses.'); return }
    setError(null)
    setLoading(true)
    setResult(null)
    try {
      const req: CompareRequest = {
        addresses: filled,
        listing_prices: prices.slice(0, filled.length).map(p => parseFloat(p) || 0).filter(Boolean),
        buyer_profile: profile,
      }
      const data = await compareProperties(req)
      setResult(data)
    } catch (e: unknown) {
      setError((e as Error).message || 'Compare failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-bold text-white">Compare Properties</h1>
        <p className="text-slate-400 text-sm mt-1">Side-by-side AI analysis for up to 3 properties.</p>
      </div>

      {/* Input form */}
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 space-y-4">
        {addresses.map((addr, i) => (
          <div key={i} className="flex gap-3">
            <div className="flex-1 space-y-2">
              <input
                type="text"
                placeholder={`Property ${String.fromCharCode(65 + i)} address`}
                value={addr}
                onChange={e => { const a = [...addresses]; a[i] = e.target.value; setAddresses(a) }}
                className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-2.5 text-white text-sm placeholder-slate-400 focus:outline-none focus:border-indigo-500"
              />
              <input
                type="number"
                placeholder="Listing price (€) — optional"
                value={prices[i]}
                onChange={e => { const p = [...prices]; p[i] = e.target.value; setPrices(p) }}
                className="w-full bg-slate-700 border border-slate-600 rounded-xl px-4 py-2 text-white text-sm placeholder-slate-400 focus:outline-none focus:border-indigo-500"
              />
            </div>
            {addresses.length > 2 && (
              <button onClick={() => removeAddress(i)} className="text-slate-400 hover:text-red-400 text-sm px-2">✕</button>
            )}
          </div>
        ))}

        <div className="flex items-center gap-3 flex-wrap">
          {addresses.length < 3 && (
            <button onClick={addAddress} className="text-sm text-indigo-400 hover:text-indigo-300 border border-indigo-600 rounded-lg px-3 py-1.5">
              + Add 3rd property
            </button>
          )}

          <select
            value={profile}
            onChange={e => setProfile(e.target.value)}
            className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none"
          >
            {PROFILES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="ml-auto bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm px-5 py-2 rounded-xl"
          >
            {loading ? 'Analysing…' : 'Compare'}
          </button>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-5">
          {/* AI comparison narrative */}
          <div className="bg-slate-800 border border-indigo-700 rounded-2xl p-5 space-y-3">
            <p className="text-xs text-indigo-400 uppercase tracking-wide font-semibold">AI Recommendation</p>
            <p className="text-white font-semibold text-base">{result.comparison.recommendation}</p>
            <p className="text-slate-300 text-sm leading-relaxed">{result.comparison.summary}</p>

            {Object.keys(result.comparison.winner_by_dimension).length > 0 && (
              <div>
                <p className="text-xs text-slate-400 mb-2">Winner by dimension:</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(result.comparison.winner_by_dimension).map(([dim, winner]) => (
                    <span key={dim} className="text-xs bg-slate-700 px-2 py-1 rounded-lg">
                      <span className="text-slate-400">{dim}:</span>{' '}
                      <span className="text-white font-medium">{winner}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Side-by-side cards */}
          <div className={`grid gap-4 ${result.analyses.length === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
            {result.analyses.map((a, i) => (
              <div key={i} className="bg-slate-800 border border-slate-700 rounded-2xl p-4 space-y-3">
                <div>
                  <p className="text-xs text-slate-400">Property {String.fromCharCode(65 + i)}</p>
                  <p className="text-sm font-medium text-white truncate">{a.address}</p>
                </div>

                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-white">{a.composite_score}</span>
                  <span className={`text-sm font-semibold ${GRADE_COLORS[a.grade] ?? 'text-slate-300'}`}>{a.grade}</span>
                </div>

                <div className="space-y-1.5 text-sm">
                  <Row label="Fair value" value={`€${a.fair_value.toLocaleString('es-ES')}`} />
                  {a.vs_listing_pct != null && (
                    <Row
                      label="vs Listing"
                      value={`${a.vs_listing_pct > 0 ? '+' : ''}${a.vs_listing_pct.toFixed(1)}%`}
                      valueClass={a.vs_listing_pct > 5 ? 'text-red-400' : a.vs_listing_pct < -5 ? 'text-emerald-400' : 'text-slate-300'}
                    />
                  )}
                  <Row label="Monthly costs" value={`€${a.hidden_costs_monthly}/mo`} />
                  <Row label="Safety" value={`${Math.round(a.safety_score)}/100`} />
                  <Row label="School" value={`${Math.round(a.school_score)}/100`} />
                  <Row
                    label="Tourist risk"
                    value={a.airbnb_risk.replace('_', ' ')}
                    valueClass={RISK_COLORS[a.airbnb_risk] ?? 'text-slate-300'}
                  />
                </div>

                {a.key_risks.length > 0 && (
                  <div>
                    <p className="text-xs text-red-400 font-semibold mb-1">Risks</p>
                    <ul className="space-y-1">
                      {a.key_risks.slice(0, 2).map((r, j) => (
                        <li key={j} className="text-xs text-slate-400 flex gap-1">
                          <span className="text-red-400 shrink-0">▲</span>{r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Row({ label, value, valueClass = 'text-slate-300' }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className={`font-medium ${valueClass}`}>{value}</span>
    </div>
  )
}
