interface Source {
  label: string
  url: string
  note?: string   // e.g. "2024 data" or "updated monthly"
}

interface Props {
  sources: Source[]
  className?: string
}

export default function SourceBadge({ sources, className = '' }: Props) {
  return (
    <div className={`flex items-center gap-2 flex-wrap ${className}`}>
      <span className="text-xs text-slate-600">Source:</span>
      {sources.map((s, i) => (
        <span key={i} className="inline-flex items-center gap-1">
          <a
            href={s.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-500 hover:text-indigo-400 underline decoration-dotted transition-colors"
          >
            {s.label}
          </a>
          {s.note && <span className="text-xs text-slate-600">({s.note})</span>}
          {i < sources.length - 1 && <span className="text-slate-700">·</span>}
        </span>
      ))}
    </div>
  )
}
