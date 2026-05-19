import type { ParkingData } from '../types/analysis'
import SourceBadge from './SourceBadge'
import { useLanguage } from '../contexts/LanguageContext'

interface Props { data: ParkingData }

export default function ParkingModule({ data }: Props) {
  const { t } = useLanguage()
  const pk = t.sections.parking
  const fmt = (n: number) => `€${n.toLocaleString('es-ES')}`

  const zoneBadgeCls: Record<string, string> = {
    zona_verde: 'bg-amber-50 border-amber-200 text-amber-700',
    zona_azul:  'bg-blue-50 border-blue-200 text-blue-700',
    free:       'bg-green-50 border-green-200 text-green-700',
    mixed:      'bg-stone-100 border-stone-300 text-stone-600',
  }

  return (
    <div className="card p-5 space-y-4">
      {/* Header */}
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>
          {pk.label}
        </p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{pk.title}</h3>
      </div>

      {/* Private parking — green badge */}
      {data.has_private_parking && (
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
          <span className="text-green-600 text-sm">✓</span>
          <div>
            <p className="text-sm font-semibold text-green-700">{pk.included}</p>
            <p className="text-xs text-green-600">{pk.includedSub}</p>
          </div>
        </div>
      )}

      {/* Zone type */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${zoneBadgeCls[data.zone_type] ?? zoneBadgeCls.mixed}`}>
          {(pk.zoneTypes as Record<string, string>)[data.zone_type] ?? data.zone_type}
        </span>
        {data.zone_monthly_eur != null && (
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {pk.streetCost} <span className="font-semibold" style={{ color: 'var(--text-main)' }}>{fmt(data.zone_monthly_eur)}/mo</span>
            {' '}
            <span style={{ color: 'var(--text-muted)' }}>({pk.streetEstimate})</span>
          </span>
        )}
      </div>

      {/* Nearby garages */}
      <div>
        <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-sub)' }}>
          {pk.garagesNearby(data.nearby_garages_count)}
        </p>
        {data.nearby_garages.length === 0 ? (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{pk.garagesNone}</p>
        ) : (
          <div className="space-y-1.5">
            {data.nearby_garages.map((g, i) => (
              <div key={i} className="flex items-center justify-between text-sm border rounded-lg px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                <div>
                  <span style={{ color: 'var(--text-main)' }}>{g.name}</span>
                  <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>{Math.round(g.distance_m)}m away</span>
                </div>
                <span className="font-semibold text-xs" style={{ color: 'var(--text-sub)' }}>{fmt(g.monthly_est_eur)}/mo</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommendation */}
      {!data.has_private_parking && (
        <div className="rounded-lg px-3 py-2.5 border" style={{ borderColor: 'var(--accent)', backgroundColor: 'var(--surface-raised, #fafaf8)' }}>
          <p className="text-xs font-medium mb-0.5" style={{ color: 'var(--text-muted)' }}>{pk.recommendation}</p>
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold" style={{ color: 'var(--accent)' }}>
              {(pk.recommendedOptions as Record<string, string>)[data.recommended_option] ?? data.recommended_option}
            </span>
            {data.recommended_monthly_eur != null && data.recommended_monthly_eur > 0 && (
              <span className="text-sm font-bold" style={{ color: 'var(--text-main)' }}>
                {fmt(data.recommended_monthly_eur)}<span className="text-xs font-normal" style={{ color: 'var(--text-muted)' }}>/mo</span>
              </span>
            )}
            {(data.recommended_monthly_eur === 0 || data.recommended_monthly_eur == null) && (
              <span className="text-sm font-bold text-green-600">Free</span>
            )}
          </div>
        </div>
      )}

      {/* Costs context */}
      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        {data.parking_needed ? pk.notInCosts : pk.notInCostsAction}
      </p>

      <SourceBadge className="mt-1" sources={[
        { label: 'OSM Overpass', url: 'https://overpass-api.de/', note: pk.source },
      ]} />
    </div>
  )
}
