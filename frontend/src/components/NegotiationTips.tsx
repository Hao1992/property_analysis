interface Props { tips: string[] }

function tipIcon(tip: string): string {
  if (tip.includes('overvalue') || tip.includes('above') || tip.includes('overpriced')) return '⚠️'
  if (tip.includes('undervalued') || tip.includes('undervalue')) return '✅'
  if (tip.includes('energy') || tip.includes('cert')) return '⚡'
  if (tip.includes('ITE') || tip.includes('age') || tip.includes('structural')) return '🔨'
  return 'ℹ️'
}

function tipColor(tip: string): string {
  if (tip.includes('overvalue') || tip.includes('above') || tip.includes('overpriced')) return 'border-amber-200 bg-amber-50'
  if (tip.includes('undervalued')) return 'border-green-200 bg-green-50'
  if (tip.includes('energy') || tip.includes('ITE') || tip.includes('structural')) return 'border-blue-200 bg-blue-50'
  return 'border-gray-200 bg-gray-50'
}

export default function NegotiationTips({ tips }: Props) {
  return (
    <div className="card p-5 space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: 'var(--accent)' }}>Before You Sign</p>
        <h3 className="font-semibold" style={{ color: 'var(--text-main)' }}>Negotiation Tips</h3>
      </div>
      <div className="space-y-3">
        {tips.map((tip, i) => (
          <div key={i} className={`flex gap-3 p-4 rounded-xl border ${tipColor(tip)}`}>
            <span className="text-lg shrink-0">{tipIcon(tip)}</span>
            <p className="text-sm" style={{ color: 'var(--text-sub)' }}>{tip}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
