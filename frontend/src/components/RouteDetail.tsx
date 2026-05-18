import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

interface Stop {
  name: string
  lat: number
  lng: number
  connections: string[]
}

interface RouteData {
  ref: string
  name: string
  from: string
  to: string
  operator: string
  colour: string
  stops: Stop[]
  total_stops: number
}

const API_BASE = import.meta.env.VITE_API_URL || ''

const stopIcon = (hasConnections: boolean) => new L.DivIcon({
  html: `<div style="background:${hasConnections ? '#f59e0b' : '#2563eb'};width:${hasConnections ? 10 : 7}px;height:${hasConnections ? 10 : 7}px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.5)"></div>`,
  className: '',
  iconAnchor: [hasConnections ? 5 : 3.5, hasConnections ? 5 : 3.5],
})

export default function RouteDetail({
  routeRef,
  routeType = 'bus',
  onClose,
}: {
  routeRef: string
  routeType?: string
  onClose: () => void
}) {
  const [data, setData] = useState<RouteData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`${API_BASE}/transit/route?ref=${encodeURIComponent(routeRef)}&route_type=${routeType}`)
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(String(e)); setLoading(false) })
  }, [routeRef, routeType])

  const centre: [number, number] | null = data?.stops.length
    ? [
        data.stops.reduce((s, x) => s + x.lat, 0) / data.stops.length,
        data.stops.reduce((s, x) => s + x.lng, 0) / data.stops.length,
      ]
    : null

  const polyline = data?.stops.map(s => [s.lat, s.lng] as [number, number]) ?? []

  return (
    <div className="fixed inset-0 z-[2000] bg-black/60 flex items-end sm:items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] flex flex-col overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-blue-600 text-white px-2.5 py-1 rounded font-mono font-bold text-sm">
                {routeRef}
              </span>
              {data && <span className="text-sm text-gray-600">{data.operator}</span>}
            </div>
            {data && (
              <p className="text-xs text-gray-500 mt-1">
                {data.from} ↔ {data.to}
                <span className="ml-2">· {data.total_stops} stops</span>
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-2xl leading-none">×</button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center py-16 text-gray-400 text-sm">
              Loading route data…
            </div>
          )}

          {error && (
            <div className="px-5 py-6 text-center text-sm text-red-500">
              Could not load route data. Try again.
            </div>
          )}

          {data && centre && (
            <>
              {/* Map */}
              <div className="border-b border-gray-100">
                <MapContainer
                  center={centre}
                  zoom={14}
                  style={{ height: 220 }}
                  scrollWheelZoom={false}
                  attributionControl={false}
                >
                  <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />

                  {/* Route polyline */}
                  {polyline.length > 1 && (
                    <Polyline
                      positions={polyline}
                      pathOptions={{ color: data.colour || '#2563eb', weight: 3, opacity: 0.8 }}
                    />
                  )}

                  {/* Stop markers */}
                  {data.stops.map((s, i) => (
                    <Marker
                      key={i}
                      position={[s.lat, s.lng]}
                      icon={stopIcon(s.connections.length > 0)}
                    >
                      <Popup>
                        <div className="text-xs">
                          <p className="font-semibold">{s.name}</p>
                          {s.connections.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              <span className="text-gray-500">Connects:</span>
                              {s.connections.map(c => (
                                <span key={c} className="bg-amber-500 text-white px-1 py-0.5 rounded font-mono font-bold text-xs">{c}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              </div>

              {/* Stop list */}
              <div className="px-5 py-3 space-y-0">
                <p className="text-xs text-gray-500 mb-2">
                  🟡 Yellow = transfer available · 🔵 Blue = regular stop
                </p>
                {data.stops.map((s, i) => (
                  <div
                    key={i}
                    className={`flex items-center justify-between py-2 border-b border-gray-50 last:border-0 ${
                      i === 0 ? 'font-semibold' : i === data.stops.length - 1 ? 'font-semibold' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`w-2 h-2 rounded-full shrink-0 ${s.connections.length > 0 ? 'bg-amber-400' : 'bg-blue-400'}`} />
                      <span className="text-sm text-gray-800 truncate">{s.name}</span>
                    </div>
                    {s.connections.length > 0 && (
                      <div className="flex gap-1 ml-2 shrink-0">
                        {s.connections.slice(0, 4).map(c => (
                          <span key={c} className="text-xs bg-amber-100 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-mono font-bold">
                            {c}
                          </span>
                        ))}
                        {s.connections.length > 4 && (
                          <span className="text-xs text-gray-400">+{s.connections.length - 4}</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
