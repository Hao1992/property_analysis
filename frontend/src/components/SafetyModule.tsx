import type { SafetyData } from '../types/analysis'
import SourceBadge from './SourceBadge'

interface Props { safety: SafetyData }

const barColor = (v: number) =>
  v >= 70 ? 'bg-green-500' : v >= 50 ? 'bg-amber-500' : 'bg-red-500'

const label = (v: number) =>
  v >= 70 ? 'Safe' : v >= 50 ? 'Moderate' : 'Elevated risk'

const INDICES = [
  { key: 'theft_rate_index',    label: 'Theft rate' },
  { key: 'vehicle_crime_index', label: 'Vehicle crime' },
  { key: 'vandalism_index',     label: 'Vandalism' },
  { key: 'night_safety_index',  label: 'Night safety' },
] as const

export default function SafetyModule({ safety }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-lg font-semibold">Safety — {safety.district}</h2>
        <span className="text-xs text-gray-400">{safety.data_year} data</span>
      </div>

      <div className="space-y-4">
        {INDICES.map(({ key, label: lbl }) => {
          const val = safety[key]
          return (
            <div key={key}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-700">{lbl}</span>
                <span className={`font-medium ${val >= 70 ? 'text-green-600' : val >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                  {val} — {label(val)}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all ${barColor(val)}`}
                  style={{ width: `${val}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-4 space-y-1">
        <p className="text-xs text-gray-400">All indices 0–100 (100 = safest). District-level data, not street-level.</p>
        <SourceBadge sources={[{ label: 'Open Data Barcelona — Seguretat Ciutadana', url: 'https://opendata-ajuntament.barcelona.cat/data/ca/dataset/estadistica-de-seguretat-ciutadana', note: `${safety.data_year} data` }]} />
      </div>
    </div>
  )
}
