import type { PoiCategory } from '../types/analysis'

interface Props { categories: PoiCategory[] }

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

export default function NeighborhoodModule({ categories }: Props) {
  // Sort: put categories with results first, then by count desc
  const sorted = [...categories].sort((a, b) => {
    if (a.total_count === 0 && b.total_count > 0) return 1
    if (a.total_count > 0 && b.total_count === 0) return -1
    return b.total_count - a.total_count
  })

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-1">Neighbourhood POIs</h2>
      <p className="text-xs text-gray-400 mb-4">Within 500m radius</p>
      <div className="grid grid-cols-2 gap-4">
        {sorted.map(cat => (
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
    </div>
  )
}
