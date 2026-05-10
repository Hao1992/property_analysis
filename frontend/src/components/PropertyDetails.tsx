import type { PropertyData } from '../types/analysis'

interface Props { property: PropertyData }

const ENERGY_COLORS: Record<string, string> = {
  A: 'bg-green-600', B: 'bg-green-500', C: 'bg-lime-500',
  D: 'bg-yellow-400', E: 'bg-orange-400', F: 'bg-red-500', G: 'bg-red-700'
}

const ITE_COLORS: Record<string, string> = {
  FAVORABLE:    'text-green-600',
  DESFAVORABLE: 'text-red-600',
  UNKNOWN:      'text-gray-400',
}

export default function PropertyDetails({ property }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">Property Details</h2>
      <div className="grid grid-cols-3 gap-4 text-sm">
        {property.surface_m2 && (
          <div><p className="text-gray-400 text-xs">Surface</p><p className="font-medium">{property.surface_m2} m²</p></div>
        )}
        {property.year_built && (
          <div><p className="text-gray-400 text-xs">Year built</p><p className="font-medium">{property.year_built}</p></div>
        )}
        {property.floor != null && (
          <div><p className="text-gray-400 text-xs">Floor</p><p className="font-medium">{property.floor === 0 ? 'Ground' : `F${property.floor}`}</p></div>
        )}
        {property.energy_cert && (
          <div>
            <p className="text-gray-400 text-xs">Energy cert</p>
            <span className={`inline-block px-2 py-0.5 rounded text-white text-xs font-bold ${ENERGY_COLORS[property.energy_cert] ?? 'bg-gray-400'}`}>
              {property.energy_cert}
            </span>
          </div>
        )}
        {property.has_lift != null && (
          <div><p className="text-gray-400 text-xs">Lift</p><p className="font-medium">{property.has_lift ? 'Yes' : 'No'}</p></div>
        )}
        {property.ite_status && (
          <div>
            <p className="text-gray-400 text-xs">ITE status</p>
            <p className={`font-medium ${ITE_COLORS[property.ite_status] ?? 'text-gray-600'}`}>{property.ite_status}</p>
          </div>
        )}
        {property.cadastral_value && (
          <div><p className="text-gray-400 text-xs">Cadastral value</p><p className="font-medium">€{property.cadastral_value.toLocaleString()}</p></div>
        )}
      </div>
    </div>
  )
}
