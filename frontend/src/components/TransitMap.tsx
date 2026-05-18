import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { PoiCategory } from '../types/analysis'

// Leaflet default icon fix for Vite
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const makeIcon = (color: string, size: number) => new L.DivIcon({
  html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,.5)"></div>`,
  className: '',
  iconAnchor: [size / 2, size / 2],
})

const METRO_ICON  = makeIcon('#dc2626', 14)
const BUS_ICON    = makeIcon('#2563eb', 10)
const HOME_ICON = new L.DivIcon({
  html: '<div style="background:#7c3aed;width:16px;height:16px;border-radius:3px;border:2px solid white;box-shadow:0 2px 5px rgba(0,0,0,.5);transform:rotate(45deg)"></div>',
  className: '', iconAnchor: [8, 8],
})

interface Props {
  lat: number
  lng: number
  metro?: PoiCategory
  busStop?: PoiCategory
}

export default function TransitMap({ lat, lng, metro, busStop }: Props) {
  const metroStops  = (metro?.top_items  ?? []).filter(s => s.lat && s.lng)
  const busStops    = (busStop?.top_items ?? []).filter(s => s.lat && s.lng)

  return (
    <div className="relative rounded-xl overflow-hidden border border-gray-200">
      <MapContainer
        center={[lat, lng]}
        zoom={15}
        style={{ height: 280 }}
        scrollWheelZoom={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution="© OpenStreetMap, © CartoDB"
        />

        {/* 500m and 200m rings */}
        <Circle center={[lat, lng]} radius={500}
          pathOptions={{ color: '#6366f1', weight: 1.5, opacity: 0.5, fillOpacity: 0.05 }} />
        <Circle center={[lat, lng]} radius={200}
          pathOptions={{ color: '#6366f1', weight: 1, opacity: 0.3, fillOpacity: 0.03 }} />

        {/* Property */}
        <Marker position={[lat, lng]} icon={HOME_ICON}>
          <Popup><b>Property</b></Popup>
        </Marker>

        {/* Metro stations */}
        {metroStops.map((s, i) => (
          <Marker key={`metro-${i}`} position={[s.lat!, s.lng!]} icon={METRO_ICON}>
            <Popup>
              <div className="text-xs space-y-0.5">
                <p className="font-semibold">🚇 {s.name}</p>
                <p className="text-gray-500">{s.distance_m}m from property</p>
                {s.routes?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {s.routes.map(r => (
                      <span key={r} className="bg-red-600 text-white px-1.5 py-0.5 rounded font-mono text-xs font-bold">{r}</span>
                    ))}
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Bus stops */}
        {busStops.map((s, i) => (
          <Marker key={`bus-${i}`} position={[s.lat!, s.lng!]} icon={BUS_ICON}>
            <Popup>
              <div className="text-xs space-y-0.5">
                <p className="font-semibold">🚌 {s.name}</p>
                <p className="text-gray-500">{s.distance_m}m from property</p>
                {s.routes?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {s.routes.map(r => (
                      <span key={r} className="bg-blue-600 text-white px-1.5 py-0.5 rounded font-mono text-xs font-bold">{r}</span>
                    ))}
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-2 left-2 z-[1000] bg-white/90 backdrop-blur rounded-lg px-2.5 py-2 text-xs shadow space-y-1">
        {(metro?.total_count ?? 0) > 0 && (
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-red-600" />
            Metro — {metro!.total_count} station{metro!.total_count !== 1 ? 's' : ''} nearby
          </div>
        )}
        {(busStop?.total_count ?? 0) > 0 && (
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-600" />
            Bus — {busStop!.total_count} stop{busStop!.total_count !== 1 ? 's' : ''} nearby
          </div>
        )}
        <div className="text-gray-400 text-[10px]">Rings: 200m · 500m</div>
      </div>
    </div>
  )
}
