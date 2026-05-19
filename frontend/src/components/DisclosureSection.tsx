import type { DisclosureItem } from '../types/analysis'
import { useLanguage } from '../contexts/LanguageContext'

interface Props { items: DisclosureItem[] }

const SEVERITY_CLASS: Record<string, string> = {
  red:    'disclosure-red',
  yellow: 'disclosure-yellow',
  green:  'disclosure-green',
  info:   'disclosure-info',
}

const SEVERITY_ICON: Record<string, string> = {
  red:    '⚠',
  yellow: '!',
  green:  '✓',
  info:   'i',
}

const SEVERITY_ICON_STYLE: Record<string, string> = {
  red:    'bg-red-100 text-red-600',
  yellow: 'bg-amber-100 text-amber-700',
  green:  'bg-emerald-100 text-emerald-700',
  info:   'bg-blue-100 text-blue-600',
}

function DisclosureCard({ item }: { item: DisclosureItem }) {
  const { t } = useLanguage()
  const cls      = SEVERITY_CLASS[item.severity] ?? SEVERITY_CLASS.info
  const iconCls  = SEVERITY_ICON_STYLE[item.severity] ?? SEVERITY_ICON_STYLE.info
  const icon     = SEVERITY_ICON[item.severity] ?? 'i'

  return (
    <div className={`${cls} p-4`}>
      <div className="flex items-start gap-3">
        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${iconCls}`}>
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-stone-100 text-stone-600">
              {t.disclosure_categories[item.category] ?? item.category}
            </span>
          </div>
          <p className="text-sm font-semibold leading-snug mb-1" style={{ color: 'var(--text-main)' }}>
            {item.title}
          </p>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-sub)' }}>{item.detail}</p>
          {item.action && (
            <div className="mt-2 flex items-start gap-1.5">
              <span className="text-xs shrink-0 mt-0.5" style={{ color: 'var(--accent)' }}>→</span>
              <p className="text-xs font-medium" style={{ color: 'var(--text-sub)' }}>{item.action}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function DisclosureSection({ items }: Props) {
  const { t } = useLanguage()

  if (!items || items.length === 0) return null

  const reds    = items.filter(i => i.severity === 'red')
  const yellows = items.filter(i => i.severity === 'yellow')
  const sorted  = [...items].sort(a => a.severity === 'red' ? -1 : a.severity === 'yellow' ? 0 : 1)

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>
            {t.sections.disclosures.label}
          </p>
          <h3 className="font-display text-xl font-semibold" style={{ color: 'var(--text-main)' }}>
            {t.sections.disclosures.title(items.length)}
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-muted)' }}>
          {reds.length > 0    && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />{t.sections.disclosures.critical(reds.length)}</span>}
          {yellows.length > 0 && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />{t.sections.disclosures.note(yellows.length)}</span>}
        </div>
      </div>
      <div className="space-y-2.5">
        {sorted.map(item => <DisclosureCard key={item.id} item={item} />)}
      </div>
    </div>
  )
}
