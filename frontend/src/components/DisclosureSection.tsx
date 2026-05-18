import type { DisclosureItem } from '../types/analysis'

interface Props { items: DisclosureItem[] }

const SEVERITY_CONFIG = {
  red:    { dot: 'bg-red-500',    badge: 'bg-red-950 border-red-800',    label: 'text-red-400',   icon: '🔴' },
  yellow: { dot: 'bg-yellow-400', badge: 'bg-yellow-950 border-yellow-800', label: 'text-yellow-400', icon: '🟡' },
  green:  { dot: 'bg-green-500',  badge: 'bg-green-950 border-green-800', label: 'text-green-400', icon: '🟢' },
  info:   { dot: 'bg-slate-400',  badge: 'bg-slate-800 border-slate-700', label: 'text-slate-400', icon: 'ℹ️' },
} as const

const CATEGORY_LABEL: Record<string, string> = {
  costs: 'Costs',
  building: 'Building',
  legal: 'Legal',
  neighborhood: 'Neighbourhood',
}

function DisclosureCard({ item }: { item: DisclosureItem }) {
  const cfg = SEVERITY_CONFIG[item.severity] ?? SEVERITY_CONFIG.info
  return (
    <div className={`border rounded-xl p-4 ${cfg.badge}`}>
      <div className="flex items-start gap-3">
        <span className="text-base mt-0.5 shrink-0">{cfg.icon}</span>
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs font-medium uppercase tracking-wide ${cfg.label}`}>
              {CATEGORY_LABEL[item.category] ?? item.category}
            </span>
          </div>
          <p className="text-sm font-semibold text-white leading-snug mb-1">{item.title}</p>
          <p className="text-xs text-slate-400 leading-relaxed">{item.detail}</p>
          {item.action && (
            <div className="mt-2 flex items-start gap-1.5">
              <span className="text-xs text-slate-500 shrink-0 mt-0.5">→</span>
              <p className="text-xs text-slate-300 leading-relaxed">{item.action}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function DisclosureSection({ items }: Props) {
  if (!items || items.length === 0) return null

  const reds    = items.filter(i => i.severity === 'red')
  const yellows = items.filter(i => i.severity === 'yellow')
  const rest    = items.filter(i => i.severity !== 'red' && i.severity !== 'yellow')

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">
          Before you sign — {items.length} thing{items.length !== 1 ? 's' : ''} to know
        </h3>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {reds.length > 0    && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />{reds.length} critical</span>}
          {yellows.length > 0 && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" />{yellows.length} note</span>}
        </div>
      </div>
      <div className="space-y-3">
        {items.map(item => <DisclosureCard key={item.id} item={item} />)}
      </div>
      {rest.length === 0 && reds.length === 0 && yellows.length === 0 && (
        <p className="text-xs text-slate-500 mt-3">No critical issues found based on available data.</p>
      )}
    </div>
  )
}
