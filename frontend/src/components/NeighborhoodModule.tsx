import { useState } from 'react'
import type { PoiCategory } from '../types/analysis'
import SourceBadge from './SourceBadge'
import TransitMap from './TransitMap'
import RouteDetail from './RouteDetail'
import { useLanguage } from '../contexts/LanguageContext'

// Barcelona bus route destinations (key routes)
const BUS_ROUTE_DESC: Record<string, string> = {
  V13: "Av.Tibidabo ↔ Barceloneta", V15: "Kennedy ↔ Catalunya",
  V17: "Av.Tibidabo ↔ Poblenou",    V19: "Av.Tibidabo ↔ Verneda",
  V23: "Sarrià ↔ Glòries",
  H4:  "Montbau ↔ Fòrum",           H6:  "Tibidabo ↔ Fòrum",
  N0:  "Catalunya ↔ Cornellà (night)", N5: "Catalunya ↔ Tibidabo (night)",
  N8:  "Catalunya ↔ Gavà (night)",   N24: "Catalunya ↔ Tibidabo (night)",
  "101": "Sarrià ↔ Eixample",       "123": "Catalunya ↔ Sarrià",
  "124": "Kennedy ↔ Castellbisbal", "125": "Catalunya ↔ Vallvidrera",
  "131": "Tibidabo ↔ Gràcia",       "196": "Sarrià ↔ Pg.Gràcia",
  "60": "Sarrià ↔ Eixample",        "64": "Sarrià ↔ Catalunya",
  "75": "Kennedy ↔ Besòs",          "76": "Gràcia ↔ Tibidabo",
}

interface Props { categories: PoiCategory[]; lat: number; lng: number }

const CATEGORY_ICONS: Record<string, string> = {
  supermarket:     '🛒',
  restaurant:      '🍽️',
  pharmacy:        '💊',
  school:          '🏫',
  park:            '🌳',
  parking:         '🅿️',
  bus_stop:        '🚌',
  metro:           '🚇',
  hospital:        '🏥',
  gym:             '🏋️',
  library:         '📚',
  cultural_centre: '🎭',
  theatre:         '🎬',
  marketplace:     '🏪',
}


const Stars = ({ rating }: { rating?: number }) => {
  if (!rating) return null
  return (
    <span className="text-yellow-400 text-xs">
      {'★'.repeat(Math.floor(rating))}
      {rating % 1 >= 0.5 ? '½' : ''}
      {'☆'.repeat(5 - Math.ceil(rating))}
      <span className="text-gray-400 ml-1">{rating.toFixed(1)}</span>
    </span>
  )
}

function CountBadge({ count, category, label }: { count: number; category: string; label: string }) {
  const color =
    category === 'supermarket' && count === 0 ? 'bg-red-100 text-red-600' :
    count === 0 ? 'bg-gray-100 text-gray-400' :
    count >= 10 ? 'bg-green-100 text-green-700' :
    'bg-blue-100 text-blue-700'

  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${color}`}>
      {label}
    </span>
  )
}

const TRANSIT_CATS = new Set(['metro', 'bus_stop'])

export default function NeighborhoodModule({ categories, lat, lng }: Props) {
  const { t } = useLanguage()
  const nb = t.sections.neighborhood
  const cats = nb.categories as Record<string, string>
  const [activeRoute, setActiveRoute] = useState<{ ref: string; type: string } | null>(null)

  const transit = categories.filter(c => TRANSIT_CATS.has(c.category))
  const amenities = categories.filter(c => !TRANSIT_CATS.has(c.category))
  const metro   = categories.find(c => c.category === 'metro')
  const busStop = categories.find(c => c.category === 'bus_stop')

  const sortedAmenities = [...amenities].sort((a, b) => {
    if (a.total_count === 0 && b.total_count > 0) return 1
    if (a.total_count > 0 && b.total_count === 0) return -1
    return b.total_count - a.total_count
  })

  // Metro first, then bus
  const sortedTransit = [...transit].sort((a) => a.category === 'metro' ? -1 : 1)

  return (
    <div className="card p-5 space-y-6">

      {/* Transit — separate prominent section */}
      {sortedTransit.some(c => c.total_count > 0) && (
        <div>
          <div className="mb-1">
            <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{nb.label}</p>
            <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{nb.transit}</h3>
          </div>
          <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>{nb.transitSub}</p>
          <TransitMap lat={lat} lng={lng} metro={metro} busStop={busStop} />

          <div className="space-y-5 mt-5">
            {/* Metro — show each station with its line */}
            {metro && metro.total_count > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">🚇</span>
                  <span className="font-medium text-sm" style={{ color: 'var(--text-main)' }}>{nb.metroTrain}</span>
                  <CountBadge count={metro.total_count} category="metro" label={nb.nearby(metro.total_count)} />
                </div>
                <div className="space-y-2">
                  {metro.top_items.map((item, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className="flex gap-1 flex-wrap">
                          {item.routes.map(r => (
                            <button key={r}
                              onClick={() => setActiveRoute({ ref: r, type: 'subway' })}
                              className="text-xs px-1.5 py-0.5 rounded font-mono font-bold text-white bg-red-600 hover:opacity-80"
                              title={`View all stops on ${r}`}
                            >{r}</button>
                          ))}
                        </div>
                        <span className="text-sm text-gray-700 truncate">{item.name}</span>
                      </div>
                      <span className="text-xs text-gray-400 shrink-0 ml-2">{item.distance_m}m</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bus — unique routes summary + nearest stops */}
            {busStop && busStop.total_count > 0 && (() => {
              // Collect all unique routes across all nearby stops
              const routeToNearest: Map<string, number> = new Map()
              for (const item of busStop.top_items) {
                for (const r of (item.routes ?? [])) {
                  if (!routeToNearest.has(r) || item.distance_m < (routeToNearest.get(r) ?? 9999)) {
                    routeToNearest.set(r, item.distance_m)
                  }
                }
              }
              const uniqueRoutes = Array.from(routeToNearest.entries())
                .sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))

              return (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">🚌</span>
                    <span className="font-medium text-sm" style={{ color: 'var(--text-main)' }}>{nb.busWithin}</span>
                    <CountBadge count={busStop.total_count} category="bus_stop" label={nb.nearby(busStop.total_count)} />
                  </div>

                  {/* Unique routes */}
                  <div className="space-y-1.5 mb-4">
                    {uniqueRoutes.map(([r, nearestM]) => {
                      const desc = BUS_ROUTE_DESC[r]
                      return (
                        <div key={r} className="flex items-center gap-2">
                          <button
                            onClick={() => setActiveRoute({ ref: r, type: 'bus' })}
                            className="text-xs px-2 py-1 rounded font-mono font-bold text-white bg-blue-600 hover:bg-blue-700 shrink-0 transition-colors"
                            title={`View all stops on route ${r}`}
                          >{r}</button>
                          <span className="text-sm text-gray-700 flex-1 truncate">{desc ?? r}</span>
                          <span className="text-xs shrink-0" style={{ color: 'var(--text-muted)' }}>{nb.nearestM(nearestM)}</span>
                        </div>
                      )
                    })}
                  </div>

                  {/* Nearest stops (no route repetition) */}
                  <div className="border-t pt-3" style={{ borderColor: 'var(--border)' }}>
                    <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{nb.nearestStops}</p>
                    <div className="space-y-1">
                      {busStop.top_items.slice(0, 4).map((item, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className="text-gray-600 truncate">{item.name}</span>
                          <span className="text-gray-400 shrink-0 ml-2">{item.distance_m}m</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })()}
          </div>
        </div>
      )}

      {/* Amenities grid */}
      <div>
        <div className="mb-1">
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>{nb.label}</p>
          <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>{nb.amenities}</h3>
        </div>
        <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>{nb.radius}</p>
        <div className="grid grid-cols-2 gap-4">
          {sortedAmenities.map(cat => (
            <div key={cat.category} className={`border rounded-xl p-4 ${cat.total_count === 0 ? 'bg-stone-50' : 'bg-white'}`} style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{CATEGORY_ICONS[cat.category] ?? '📍'}</span>
                  <span className="font-medium text-sm" style={{ color: 'var(--text-main)' }}>{cats[cat.category] ?? cat.category}</span>
                </div>
                <CountBadge count={cat.total_count} category={cat.category} label={nb.nearby(cat.total_count)} />
              </div>

              {cat.avg_rating && (
                <div className="mb-3 flex items-center gap-2">
                  <Stars rating={cat.avg_rating} />
                  {cat.total_reviews && (
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>({cat.total_reviews.toLocaleString()} {nb.reviews})</span>
                  )}
                </div>
              )}

              {cat.top_items.length > 0 ? (
                <div className="space-y-2.5">
                  {cat.top_items.map((item, i) => (
                    <div key={i} className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium truncate" style={{ color: 'var(--text-main)' }}>{item.name}</p>
                        {item.google_rating && <Stars rating={item.google_rating} />}
                        {item.routes && item.routes.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {item.routes.slice(0, 8).map(r => (
                              <span key={r} className="text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded font-mono font-bold">{r}</span>
                            ))}
                            {item.routes.length > 8 && (
                              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{nb.moreRoutes(item.routes.length - 8)}</span>
                            )}
                          </div>
                        )}
                      </div>
                      <span className="text-xs shrink-0 mt-0.5" style={{ color: 'var(--text-muted)' }}>{item.distance_m}m</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>{nb.noneFound}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      <SourceBadge sources={[{ label: 'OpenStreetMap via Overpass API', url: 'https://overpass-turbo.eu/', note: 'POI locations within 500m' }]} />

      {/* Route detail modal */}
      {activeRoute && (
        <RouteDetail
          routeRef={activeRoute.ref}
          routeType={activeRoute.type}
          onClose={() => setActiveRoute(null)}
        />
      )}
    </div>
  )
}
