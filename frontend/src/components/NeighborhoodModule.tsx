import { useState } from 'react'
import type { PoiCategory } from '../types/analysis'
import SourceBadge from './SourceBadge'
import TransitMap from './TransitMap'
import RouteDetail from './RouteDetail'

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

const CATEGORY_LABELS: Record<string, string> = {
  supermarket:     'Supermarket',
  restaurant:      'Restaurant / Café',
  pharmacy:        'Pharmacy',
  school:          'School',
  park:            'Park / Garden',
  parking:         'Parking',
  bus_stop:        'Bus Stop',
  metro:           'Metro',
  hospital:        'Hospital / Clinic',
  gym:             'Gym / Sports',
  library:         'Library',
  cultural_centre: 'Cultural Centre',
  theatre:         'Theatre / Cinema',
  marketplace:     'Market',
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

const CountBadge = ({ count, category }: { count: number; category: string }) => {
  const color =
    category === 'supermarket' && count === 0 ? 'bg-red-100 text-red-600' :
    count === 0 ? 'bg-gray-100 text-gray-400' :
    count >= 10 ? 'bg-green-100 text-green-700' :
    'bg-blue-100 text-blue-700'

  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${color}`}>
      {count} nearby
    </span>
  )
}

const TRANSIT_CATS = new Set(['metro', 'bus_stop'])

export default function NeighborhoodModule({ categories, lat, lng }: Props) {
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
    <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-6">

      {/* Transit — separate prominent section */}
      {sortedTransit.some(c => c.total_count > 0) && (
        <div>
          <h2 className="text-lg font-semibold mb-1">Public Transport</h2>
          <p className="text-xs text-gray-400 mb-4">Click route badge to see all stops · 500m radius</p>
          <TransitMap lat={lat} lng={lng} metro={metro} busStop={busStop} />

          <div className="space-y-5 mt-5">
            {/* Metro — show each station with its line */}
            {metro && metro.total_count > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">🚇</span>
                  <span className="font-medium text-sm">Metro / Train</span>
                  <CountBadge count={metro.total_count} category="metro" />
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
                    <span className="font-medium text-sm">Bus routes within 500m</span>
                    <CountBadge count={busStop.total_count} category="bus_stop" />
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
                          <span className="text-xs text-gray-400 shrink-0">nearest {nearestM}m</span>
                        </div>
                      )
                    })}
                  </div>

                  {/* Nearest stops (no route repetition) */}
                  <div className="border-t border-gray-100 pt-3">
                    <p className="text-xs text-gray-400 mb-2">Nearest stops</p>
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
        <h2 className="text-lg font-semibold mb-1">Neighbourhood Amenities</h2>
        <p className="text-xs text-gray-400 mb-4">Within 500m radius</p>
      <div className="grid grid-cols-2 gap-4">
        {sortedAmenities.map(cat => (
          <div key={cat.category} className={`border rounded-xl p-4 ${cat.total_count === 0 ? 'border-gray-100 bg-gray-50' : 'border-gray-100'}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">{CATEGORY_ICONS[cat.category] ?? '📍'}</span>
                <span className="font-medium text-sm">{CATEGORY_LABELS[cat.category] ?? cat.category}</span>
              </div>
              <CountBadge count={cat.total_count} category={cat.category} />
            </div>

            {/* Category avg rating */}
            {cat.avg_rating && (
              <div className="mb-3 flex items-center gap-2">
                <Stars rating={cat.avg_rating} />
                {cat.total_reviews && (
                  <span className="text-xs text-gray-400">({cat.total_reviews.toLocaleString()} reviews)</span>
                )}
              </div>
            )}

            {/* Top items */}
            {cat.top_items.length > 0 ? (
              <div className="space-y-2.5">
                {cat.top_items.map((item, i) => (
                  <div key={i} className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-gray-800 truncate">{item.name}</p>
                      {item.google_rating && <Stars rating={item.google_rating} />}
                      {/* Transit route numbers */}
                      {item.routes && item.routes.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {item.routes.slice(0, 8).map(r => (
                            <span key={r} className="text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded font-mono font-bold">
                              {r}
                            </span>
                          ))}
                          {item.routes.length > 8 && (
                            <span className="text-xs text-gray-400">+{item.routes.length - 8} more</span>
                          )}
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-gray-400 shrink-0 mt-0.5">{item.distance_m}m</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-400 italic">None found within 500m</p>
            )}
          </div>
        ))}
      </div>
      </div>  {/* end amenities */}

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
