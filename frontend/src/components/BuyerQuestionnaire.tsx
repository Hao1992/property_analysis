import { useState } from 'react'
import type { UserAnswers } from '../types/analysis'

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
        <p className="text-sm font-medium text-slate-200">{label}</p>
        {hint && <p className="text-xs text-slate-500">{hint}</p>}
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
                  ? 'bg-indigo-600 border-indigo-500 text-white'
                  : 'bg-slate-700 border-slate-600 text-slate-300 hover:border-slate-400'
                }`}
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
  const [open, setOpen] = useState(false)
  const hasAnswers = Object.values(value).some(v => v !== undefined && v !== null)

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
      >
        <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        <span>
          {hasAnswers
            ? `Buyer profile customised (${Object.values(value).filter(v => v !== undefined).length}/8 answered)`
            : 'Customise buyer profile'}
          <span className="text-xs text-slate-500 ml-1">— affects score weights</span>
        </span>
      </button>

      {open && (
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-4 space-y-5">
          <p className="text-xs text-slate-500">
            Your answers adjust which dimensions matter most. Unanswered questions use balanced defaults.
          </p>

          <Q
            label="Do you have children living with you?"
            opts={[
              { value: 'none',  label: 'No children' },
              { value: 'young', label: 'Young (0-12)', icon: '🧒' },
              { value: 'teen',  label: 'Teenager (13-18)', icon: '🧑' },
            ]}
            value={value.children_age}
            onChange={v => onChange({ ...value, children_age: v })}
          />

          <Q
            label="How long do you plan to stay?"
            opts={[
              { value: 'short',  label: 'Under 5 years' },
              { value: 'medium', label: '5 – 15 years' },
              { value: 'long',   label: '15+ years' },
            ]}
            value={value.stay_duration}
            onChange={v => onChange({ ...value, stay_duration: v })}
          />

          <Q
            label="Do you drive and need parking?"
            opts={[
              { value: false, label: 'No car', icon: '🚇' },
              { value: true,  label: 'Yes, need parking', icon: '🚗' },
            ]}
            value={value.has_car}
            onChange={v => onChange({ ...value, has_car: v })}
          />

          <Q
            label="Will you rent this property out?"
            opts={[
              { value: 'none',       label: 'No, owner-occupied' },
              { value: 'long_term',  label: 'Long-term rental', icon: '🏠' },
              { value: 'short_term', label: 'Short-term / Airbnb', icon: '🏖️' },
            ]}
            value={value.rental_intent}
            onChange={v => onChange({ ...value, rental_intent: v })}
          />

          <Q
            label="How sensitive are you to nightlife noise?"
            opts={[
              { value: 'love_it',    label: 'I like city life', icon: '🎶' },
              { value: 'neutral',    label: 'Neutral' },
              { value: 'need_quiet', label: 'Need quiet nights', icon: '😴' },
            ]}
            value={value.noise_tolerance}
            onChange={v => onChange({ ...value, noise_tolerance: v })}
          />

          <Q
            label="Where do you primarily work?"
            opts={[
              { value: 'home',    label: 'From home', icon: '💻' },
              { value: 'commute', label: 'Daily commute', icon: '🚇' },
              { value: 'retired', label: 'Retired / no commute', icon: '🌴' },
            ]}
            value={value.work_situation}
            onChange={v => onChange({ ...value, work_situation: v })}
          />

          <Q
            label="Renovation comfort?"
            hint="How much work are you willing to take on?"
            opts={[
              { value: 'ready',          label: 'Full renovation OK', icon: '🔨' },
              { value: 'minor',          label: 'Minor works fine' },
              { value: 'move_in_ready',  label: 'Move-in ready only', icon: '✨' },
            ]}
            value={value.renovation_appetite}
            onChange={v => onChange({ ...value, renovation_appetite: v })}
          />

          <Q
            label="How important is local culture & neighbourhood character?"
            opts={[
              { value: 'important',     label: 'Very important', icon: '🎭' },
              { value: 'neutral',       label: 'Neutral' },
              { value: 'not_important', label: 'Not a priority' },
            ]}
            value={value.lifestyle_priority}
            onChange={v => onChange({ ...value, lifestyle_priority: v })}
          />

          {hasAnswers && (
            <button
              type="button"
              onClick={() => onChange({})}
              className="text-xs text-slate-500 hover:text-red-400 transition-colors"
            >
              Reset all answers
            </button>
          )}
        </div>
      )}
    </div>
  )
}
