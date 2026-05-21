import type { ParkingData } from '../types/analysis'
import SourceBadge from './SourceBadge'
import { useLanguage } from '../contexts/LanguageContext'

interface Props { data: ParkingData }

export default function ParkingModule({ data }: Props) {
  const { t } = useLanguage()
  const pk = t.sections.parking
  const fmt = (n: number) => `€${n.toLocaleString('es-ES')}`
  const officialSegments = data.official_segments ?? []
  const garageList = data.nearby_garages_unpriced ?? data.nearby_garages ?? []
  const garageCount = data.nearby_garages_unpriced_count ?? data.nearby_garages_count

  const zoneBadgeCls: Record<string, string> = {
    zona_verde: 'bg-amber-50 border-amber-200 text-amber-700',
    zona_azul:  'bg-blue-50 border-blue-200 text-blue-700',
    resident:   'bg-slate-100 border-slate-300 text-slate-700',
    dum:        'bg-yellow-50 border-yellow-200 text-yellow-800',
    free:       'bg-green-50 border-green-200 text-green-700',
    mixed:      'bg-stone-100 border-stone-300 text-stone-600',
    unknown:    'bg-slate-50 border-slate-200 text-slate-500',
  }
  const zoneLabel = (zone: string) => (pk.zoneTypes as Record<string, string>)[zone] ?? zone
  const sourceNote = data.official_data_last_modified
    ? `${pk.source}; ${data.official_data_last_modified}`
    : pk.source

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
          {zoneLabel(data.zone_type)}
        </span>
        {data.resident_zone && (
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {pk.residentZone(data.resident_zone)}
          </span>
        )}
        {(data.street_tariff || data.street_timetable) && (
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {pk.streetCost}{' '}
            <span className="font-semibold" style={{ color: 'var(--text-main)' }}>
              {data.street_tariff ?? pk.tariffUnavailable}
            </span>
          </span>
        )}
      </div>

      {officialSegments.length > 0 && (
        <div>
          <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-sub)' }}>
            {pk.officialSegments}
          </p>
          <div className="space-y-1.5">
            {officialSegments.slice(0, 5).map((seg, i) => (
              <div key={`${seg.zone_type}-${seg.location}-${i}`} className="border rounded-lg px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${zoneBadgeCls[seg.zone_type] ?? zoneBadgeCls.unknown}`}>
                        {zoneLabel(seg.zone_type)}
                      </span>
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {Math.round(seg.distance_m)}{pk.distAway}
                      </span>
                    </div>
                    <p className="text-sm mt-1 truncate" style={{ color: 'var(--text-main)' }}>
                      {seg.location ?? zoneLabel(seg.zone_type)}
                    </p>
                  </div>
                  {seg.places && (
                    <span className="shrink-0 text-xs" style={{ color: 'var(--text-muted)' }}>
                      {pk.spaces(seg.places)}
                    </span>
                  )}
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--text-sub)' }}>
                  {seg.tariff ?? pk.tariffUnavailable}
                </p>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                  {seg.timetable ?? pk.timetableUnavailable}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Nearby garages */}
      <div>
        <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-sub)' }}>
          {pk.garagesNearby(garageCount)}
        </p>
        {garageList.length === 0 ? (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{pk.garagesNone}</p>
        ) : (
          <div className="space-y-1.5">
            {garageList.map((g, i) => (
              <div key={i} className="flex items-center justify-between text-sm border rounded-lg px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                <div>
                  <span style={{ color: 'var(--text-main)' }}>{g.name}</span>
                  <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>{Math.round(g.distance_m)}{pk.distAway}</span>
                </div>
                <span className="font-semibold text-xs" style={{ color: 'var(--text-sub)' }}>
                  {g.monthly_est_eur != null ? `${fmt(g.monthly_est_eur)}${pk.perMonth}` : pk.priceUnavailable}
                </span>
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
                {fmt(data.recommended_monthly_eur)}<span className="text-xs font-normal" style={{ color: 'var(--text-muted)' }}>{pk.perMonth}</span>
              </span>
            )}
            {data.recommended_option === 'free' && data.recommended_monthly_eur === 0 && (
              <span className="text-sm font-bold text-green-600">{pk.zoneTypes.free}</span>
            )}
            {(data.recommended_monthly_eur == null || data.recommended_monthly_eur < 0) && (
              <span className="text-sm font-semibold" style={{ color: 'var(--text-muted)' }}>{pk.noVerifiedPrice}</span>
            )}
          </div>
        </div>
      )}

      {/* Costs context */}
      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        {data.parking_needed ? pk.notInCosts : pk.notInCostsAction}
      </p>

      <SourceBadge className="mt-1" sources={[
        { label: 'Area Verda', url: data.official_source_url ?? 'https://areaverda.cat/en/map', note: sourceNote },
        { label: 'OSM Overpass', url: 'https://overpass-api.de/', note: pk.garagesNearby(garageCount) },
      ]} />
    </div>
  )
}
