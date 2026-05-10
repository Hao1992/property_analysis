import { useState } from 'react'
import type { AnalyzeRequest } from '../types/analysis'

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
  const [listingPrice, setListingPrice] = useState('')
  const [profile, setProfile] = useState<AnalyzeRequest['buyer_profile']>('balanced')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!address.trim()) return
    const parsedPrice = listingPrice ? parseFloat(listingPrice.replace(/[.,\s]/g, '').replace(',', '.')) : NaN
    onSubmit({
      address: address.trim(),
      listing_price: !isNaN(parsedPrice) && parsedPrice > 0 ? parsedPrice : undefined,
      buyer_profile: profile,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-slate-800 border border-slate-700 rounded-2xl p-6 space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">Property address</label>
        <input
          type="text"
          value={address}
          onChange={e => setAddress(e.target.value)}
          placeholder="e.g. Carrer de Mallorca 401, Barcelona"
          className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-sm"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
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
