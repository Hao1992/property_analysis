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
    const parsedPrice = listingPrice ? parseFloat(listingPrice.replace(/[.,\s]/g, '').replace(',', '.')) : NaN
    const parsedYear  = yearBuilt ? parseInt(yearBuilt, 10) : NaN
    const parsedFloor = floor !== '' ? parseInt(floor, 10) : NaN
    const hasAnswers  = Object.values(userAnswers).some(v => v !== undefined)
    onSubmit({
      address: address.trim(),
      listing_price: !isNaN(parsedPrice) && parsedPrice > 0 ? parsedPrice : undefined,
      buyer_profile: profile,
      user_answers: hasAnswers ? userAnswers : undefined,
      year_built: !isNaN(parsedYear) && parsedYear > 1800 && parsedYear <= new Date().getFullYear() ? parsedYear : undefined,
      floor: !isNaN(parsedFloor) && parsedFloor >= 0 ? parsedFloor : undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-slate-800 border border-slate-700 rounded-2xl p-6 space-y-4">
      <div className="relative">
        <label className="block text-sm font-medium text-slate-300 mb-1">Property address</label>
        <input
          type="text"
          value={address}
          onChange={e => { setAddress(e.target.value); setShowSugg(true) }}
          onBlur={() => setTimeout(() => setShowSugg(false), 150)}
          onFocus={() => suggestions.length > 0 && setShowSugg(true)}
          placeholder="e.g. Carrer de Mallorca 401, Barcelona"
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm"
          required
          autoComplete="off"
        />
        {showSugg && suggestions.length > 0 && (
          <ul className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-600 rounded-xl shadow-xl overflow-hidden">
            {suggestions.map((s, i) => (
              <li
                key={i}
                onMouseDown={() => { setAddress(s); setSuggestions([]); setShowSugg(false) }}
                className="px-4 py-2.5 text-sm text-slate-200 hover:bg-slate-700 cursor-pointer border-b border-slate-700 last:border-0 truncate"
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
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Listing price (€) <span className="text-slate-500 font-normal">optional</span>
          </label>
          <input
            type="number"
            value={listingPrice}
            onChange={e => setListingPrice(e.target.value)}
            placeholder="e.g. 450000"
            min={0}
            className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Year built <span className="text-slate-500 font-normal">optional</span>
          </label>
          <input
            type="number"
            value={yearBuilt}
            onChange={e => setYearBuilt(e.target.value)}
            placeholder="e.g. 1975"
            min={1800}
            max={new Date().getFullYear()}
            className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Floor <span className="text-slate-500 font-normal">optional (affects noise)</span>
          </label>
          <input
            type="number"
            value={floor}
            onChange={e => setFloor(e.target.value)}
            placeholder="e.g. 3"
            min={0}
            max={50}
            className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Buyer profile</label>
          <select
            value={profile}
            onChange={e => setProfile(e.target.value as AnalyzeRequest['buyer_profile'])}
            className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm"
          >
            {PROFILES.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
      </div>

      <BuyerQuestionnaire value={userAnswers} onChange={setUserAnswers} />

      <button
        type="submit"
        disabled={loading || !address.trim()}
        className="w-full py-3 px-6 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors text-sm"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Analysing… (may take 30–60s)
          </span>
        ) : 'Analyse property'}
      </button>
    </form>
  )
}
