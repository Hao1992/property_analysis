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
  const hasAnyData = property.surface_m2 || property.year_built || property.floor != null
    || property.energy_cert || property.has_lift != null || property.ite_status || property.cadastral_value

  if (!hasAnyData) return null

  return (
    <div className="card p-5">
      <div className="mb-3">
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>From Catastro</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>Property Details</h3>
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 text-sm">
        {property.surface_m2 && (
          <div className="bg-stone-50 rounded-xl p-3 border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Surface</p>
            <p className="font-semibold" style={{ color: 'var(--text-main)' }}>{property.surface_m2} m²</p>
          </div>
        )}
        {property.year_built && (
          <div className="bg-stone-50 rounded-xl p-3 border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Year built</p>
            <p className="font-semibold" style={{ color: 'var(--text-main)' }}>{property.year_built}</p>
          </div>
        )}
        {property.floor != null && (
          <div className="bg-stone-50 rounded-xl p-3 border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Floor</p>
            <p className="font-semibold" style={{ color: 'var(--text-main)' }}>{property.floor === 0 ? 'Ground' : `F${property.floor}`}</p>
          </div>
        )}
        {property.energy_cert && (
          <div className="bg-stone-50 rounded-xl p-3 border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Energy cert</p>
            <span className={`inline-block px-2 py-0.5 rounded text-white text-xs font-bold ${ENERGY_COLORS[property.energy_cert] ?? 'bg-stone-400'}`}>
              {property.energy_cert}
            </span>
          </div>
        )}
        {property.has_lift != null && (
          <div className="bg-stone-50 rounded-xl p-3 border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Lift</p>
            <p className="font-semibold" style={{ color: 'var(--text-main)' }}>{property.has_lift ? 'Yes' : 'No'}</p>
          </div>
        )}
        {property.ite_status && property.ite_status !== 'UNKNOWN' && (
          <div className="bg-stone-50 rounded-xl p-3 border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>ITE status</p>
            <p className={`font-semibold ${ITE_COLORS[property.ite_status] ?? ''}`} style={!ITE_COLORS[property.ite_status] ? { color: 'var(--text-main)' } : undefined}>
              {property.ite_status}
            </p>
          </div>
        )}
        {property.cadastral_value && (
          <div className="bg-stone-50 rounded-xl p-3 border" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Cadastral value</p>
            <p className="font-semibold" style={{ color: 'var(--text-main)' }}>€{property.cadastral_value.toLocaleString()}</p>
          </div>
        )}
      </div>
    </div>
  )
}
