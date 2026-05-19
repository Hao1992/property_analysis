import { useState } from 'react'
import type { UserAnswers } from '../types/analysis'
import { useLanguage } from '../contexts/LanguageContext'

interface Props {
  value: UserAnswers
  onChange: (v: UserAnswers) => void
}

type Opt<T extends string | boolean> = { label: string; value: T; icon?: string }

function Q<T extends string | boolean>({
  label, hint, opts, value, onChange,
}: {
  label: string
  hint?: string
  opts: Opt<T>[]
  value: T | undefined
  onChange: (v: T) => void
}) {
  return (
    <div className="space-y-1.5">
      <div>
        <p className="text-sm font-medium" style={{ color: 'var(--text-main)' }}>{label}</p>
        {hint && <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{hint}</p>}
      </div>
      <div className="flex flex-wrap gap-2">
        {opts.map(opt => {
          const active = value === opt.value
          return (
            <button
              key={String(opt.value)}
              type="button"
              onClick={() => onChange(opt.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                ${active
                  ? 'text-white border-transparent'
                  : 'bg-white hover:bg-stone-50'
                }`}
              style={active
                ? { backgroundColor: 'var(--accent)', borderColor: 'var(--accent)' }
                : { borderColor: 'var(--border)', color: 'var(--text-sub)' }
              }
            >
              {opt.icon && <span className="mr-1">{opt.icon}</span>}{opt.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function BuyerQuestionnaire({ value, onChange }: Props) {
  const { t } = useLanguage()
  const q = t.questionnaire
  const [open, setOpen] = useState(false)
  const answerCount = Object.values(value).filter(v => v !== undefined).length
  const hasAnswers = answerCount > 0

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 text-sm transition-colors hover:opacity-80"
        style={{ color: 'var(--text-muted)' }}
      >
        <span className={`transition-transform text-xs ${open ? 'rotate-90' : ''}`}>▶</span>
        <span>
          {hasAnswers ? q.toggleDone(answerCount) : q.toggle}
          <span className="text-xs ml-1" style={{ color: 'var(--text-muted)' }}>{q.toggleSub}</span>
        </span>
      </button>

      {open && (
        <div className="bg-stone-50 border rounded-xl p-4 space-y-5" style={{ borderColor: 'var(--border)' }}>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{q.hint}</p>

          <Q label={q.questions.children.label}
            opts={q.questions.children.opts as unknown as Opt<string>[]}
            value={value.children_age}
            onChange={v => onChange({ ...value, children_age: v as 'none' | 'young' | 'teen' })}
          />
          <Q label={q.questions.stay.label}
            opts={q.questions.stay.opts as unknown as Opt<string>[]}
            value={value.stay_duration}
            onChange={v => onChange({ ...value, stay_duration: v as 'short' | 'medium' | 'long' })}
          />
          <Q label={q.questions.car.label}
            opts={q.questions.car.opts as unknown as Opt<boolean>[]}
            value={value.has_car}
            onChange={v => onChange({ ...value, has_car: v as boolean })}
          />
          <Q label={q.questions.rental.label}
            opts={q.questions.rental.opts as unknown as Opt<string>[]}
            value={value.rental_intent}
            onChange={v => onChange({ ...value, rental_intent: v as 'none' | 'long_term' | 'short_term' })}
          />
          <Q label={q.questions.noise.label}
            opts={q.questions.noise.opts as unknown as Opt<string>[]}
            value={value.noise_tolerance}
            onChange={v => onChange({ ...value, noise_tolerance: v as 'love_it' | 'neutral' | 'need_quiet' })}
          />
          <Q label={q.questions.work.label}
            opts={q.questions.work.opts as unknown as Opt<string>[]}
            value={value.work_situation}
            onChange={v => onChange({ ...value, work_situation: v as 'home' | 'commute' | 'retired' })}
          />
          <Q label={q.questions.renovation.label}
            hint={q.questions.renovation.hint}
            opts={q.questions.renovation.opts as unknown as Opt<string>[]}
            value={value.renovation_appetite}
            onChange={v => onChange({ ...value, renovation_appetite: v as 'ready' | 'minor' | 'move_in_ready' })}
          />
          <Q label={q.questions.lifestyle.label}
            opts={q.questions.lifestyle.opts as unknown as Opt<string>[]}
            value={value.lifestyle_priority}
            onChange={v => onChange({ ...value, lifestyle_priority: v as 'important' | 'neutral' | 'not_important' })}
          />

          {hasAnswers && (
            <button
              type="button"
              onClick={() => onChange({})}
              className="text-xs hover:text-red-500 transition-colors"
              style={{ color: 'var(--text-muted)' }}
            >
              {q.reset}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
