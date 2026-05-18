import { useState, useEffect, useRef } from 'react'
import type { AnalyzeRequest, UserAnswers } from '../types/analysis'
import BuyerQuestionnaire from './BuyerQuestionnaire'

interface Props {
  onSubmit: (req: AnalyzeRequest) => void
  loading: boolean
}

const PROFILES = [
  { value: 'balanced',  label: 'Balanced' },
  { value: 'family',    label: 'Family' },
  { value: 'investor',  label: 'Investor' },
  { value: 'retiree',   label: 'Retiree' },
  { value: 'expat',     label: 'Expat / International' },
] as const

export default function AddressInput({ onSubmit, loading }: Props) {
  const [address, setAddress] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSugg, setShowSugg] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [listingPrice, setListingPrice] = useState('')
  const [profile, setProfile] = useState<AnalyzeRequest['buyer_profile']>('balanced')
  const [yearBuilt, setYearBuilt] = useState('')
  const [floor, setFloor] = useState('')
  const [surfaceM2, setSurfaceM2] = useState('')
  const [energyCert, setEnergyCert] = useState('')
  const [condition, setCondition] = useState<AnalyzeRequest['condition'] | ''>('')
  const [showPropDetails, setShowPropDetails] = useState(false)
  const [userAnswers, setUserAnswers] = useState<UserAnswers>({})

  useEffect(() => {
    if (address.length < 5) { setSuggestions([]); return }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const q = encodeURIComponent(address + (address.toLowerCase().includes('barcelona') ? '' : ', Barcelona'))
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${q}&format=json&limit=5&addressdetails=1&countrycodes=es`,
          { headers: { 'Accept-Language': 'en' } }
        )
        const data = await res.json()
        const names: string[] = data
          .filter((r: { display_name?: string; address?: { road?: string; house_number?: string } }) =>
            r.address?.road && r.address?.house_number
          )
          .map((r: { display_name?: string }) => r.display_name || '')
          .filter(Boolean)
        setSuggestions(names)
        setShowSugg(names.length > 0)
      } catch { /* silent */ }
    }, 400)
  }, [address])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!address.trim()) return
    const parsedPrice   = listingPrice ? parseFloat(listingPrice.replace(/[.,\s]/g, '').replace(',', '.')) : NaN
    const parsedYear    = yearBuilt ? parseInt(yearBuilt, 10) : NaN
    const parsedFloor   = floor !== '' ? parseInt(floor, 10) : NaN
    const parsedSurface = surfaceM2 ? parseFloat(surfaceM2) : NaN
    const hasAnswers    = Object.values(userAnswers).some(v => v !== undefined)
    onSubmit({
      address: address.trim(),
      listing_price: !isNaN(parsedPrice) && parsedPrice > 0 ? parsedPrice : undefined,
      buyer_profile: profile,
      user_answers: hasAnswers ? userAnswers : undefined,
      year_built:  !isNaN(parsedYear)    && parsedYear > 1800  ? parsedYear    : undefined,
      floor:       !isNaN(parsedFloor)   && parsedFloor >= 0   ? parsedFloor   : undefined,
      surface_m2:  !isNaN(parsedSurface) && parsedSurface > 0  ? parsedSurface : undefined,
      energy_cert: energyCert || undefined,
      condition:   (condition as AnalyzeRequest['condition']) || undefined,
    })
  }

  const inputCls = "w-full px-4 py-3 bg-stone-50 border rounded-xl text-sm outline-none transition-all focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300"
  const labelCls = "block text-sm font-medium mb-1"

  return (
    <form onSubmit={handleSubmit} className="card p-6 space-y-5">
      <div className="relative">
        <label className={labelCls} style={{ color: 'var(--text-sub)' }}>Property address</label>
        <input
          type="text"
          value={address}
          onChange={e => { setAddress(e.target.value); setShowSugg(true) }}
          onBlur={() => setTimeout(() => setShowSugg(false), 150)}
          onFocus={() => suggestions.length > 0 && setShowSugg(true)}
          placeholder="e.g. Carrer de Mallorca 401, Barcelona"
          className={inputCls}
          style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
          required
          autoComplete="off"
        />
        {showSugg && suggestions.length > 0 && (
          <ul className="absolute z-50 w-full mt-1 bg-white border rounded-xl shadow-xl overflow-hidden" style={{ borderColor: 'var(--border)' }}>
            {suggestions.map((s, i) => (
              <li
                key={i}
                onMouseDown={() => { setAddress(s); setSuggestions([]); setShowSugg(false) }}
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

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div>
          <label className={labelCls} style={{ color: 'var(--text-sub)' }}>
            Listing price (€) <span className="font-normal text-xs" style={{ color: 'var(--text-muted)' }}>optional</span>
          </label>
          <input
            type="number"
            value={listingPrice}
            onChange={e => setListingPrice(e.target.value)}
            placeholder="e.g. 450000"
            min={0}
            className={inputCls}
            style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
          />
        </div>

        <div>
          <label className={labelCls} style={{ color: 'var(--text-sub)' }}>
            Year built <span className="font-normal text-xs" style={{ color: 'var(--text-muted)' }}>optional</span>
          </label>
          <input
            type="number"
            value={yearBuilt}
            onChange={e => setYearBuilt(e.target.value)}
            placeholder="e.g. 1975"
            min={1800}
            max={new Date().getFullYear()}
            className={inputCls}
            style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
          />
        </div>

        <div>
          <label className={labelCls} style={{ color: 'var(--text-sub)' }}>
            Floor <span className="font-normal text-xs" style={{ color: 'var(--text-muted)' }}>optional</span>
          </label>
          <input
            type="number"
            value={floor}
            onChange={e => setFloor(e.target.value)}
            placeholder="e.g. 3"
            min={0}
            max={50}
            className={inputCls}
            style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
          />
        </div>

        <div>
          <label className={labelCls} style={{ color: 'var(--text-sub)' }}>Buyer profile</label>
          <select
            value={profile}
            onChange={e => setProfile(e.target.value as AnalyzeRequest['buyer_profile'])}
            className={inputCls}
            style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
          >
            {PROFILES.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Property details — collapsible */}
      <div className="space-y-3">
        <button
          type="button"
          onClick={() => setShowPropDetails(o => !o)}
          className="flex items-center gap-2 text-sm transition-colors hover:opacity-80"
          style={{ color: 'var(--text-muted)' }}
        >
          <span className={`transition-transform text-xs ${showPropDetails ? 'rotate-90' : ''}`}>▶</span>
          <span>
            Property details{' '}
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>— surface area, energy cert, condition</span>
          </span>
        </button>

        {showPropDetails && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-stone-50 border rounded-xl p-4" style={{ borderColor: 'var(--border)' }}>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-sub)' }}>
                Surface area (m²)
              </label>
              <input
                type="number"
                value={surfaceM2}
                onChange={e => setSurfaceM2(e.target.value)}
                placeholder="e.g. 85"
                min={20} max={1000}
                className="w-full px-3 py-2.5 bg-white border rounded-xl text-sm outline-none focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300"
                style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-sub)' }}>
                Energy certificate
              </label>
              <select
                value={energyCert}
                onChange={e => setEnergyCert(e.target.value)}
                className="w-full px-3 py-2.5 bg-white border rounded-xl text-sm outline-none focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300"
                style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
              >
                <option value="">Unknown</option>
                {['A','B','C','D','E','F','G'].map(c => (
                  <option key={c} value={c}>{c} {c === 'A' ? '(best)' : c === 'G' ? '(worst)' : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--text-sub)' }}>
                Condition
              </label>
              <select
                value={condition}
                onChange={e => setCondition(e.target.value as AnalyzeRequest['condition'] | '')}
                className="w-full px-3 py-2.5 bg-white border rounded-xl text-sm outline-none focus:ring-2 focus:ring-amber-300/50 focus:border-amber-300"
                style={{ borderColor: 'var(--border)', color: 'var(--text-main)' }}
              >
                <option value="">Unknown</option>
                <option value="renovated">Fully renovated</option>
                <option value="good">Good condition</option>
                <option value="needs_work">Needs renovation</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <BuyerQuestionnaire value={userAnswers} onChange={setUserAnswers} />

      <button
        type="submit"
        disabled={loading || !address.trim()}
        className="w-full py-3.5 px-6 disabled:opacity-50 text-white font-semibold rounded-xl transition-all text-sm hover:opacity-90 active:scale-[0.99]"
        style={{ backgroundColor: 'var(--accent)' }}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Analysing… (may take 30–60s)
          </span>
        ) : 'Analyse this property →'}
      </button>
    </form>
  )
}
