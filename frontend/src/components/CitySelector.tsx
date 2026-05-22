import { useLanguage } from '../contexts/LanguageContext'

export type City = 'barcelona' | 'madrid' | 'valencia'

const CITIES: { value: City; en: string; zh: string; shortEn: string; shortZh: string }[] = [
  { value: 'barcelona', en: 'Barcelona', zh: '巴塞罗那', shortEn: 'BCN', shortZh: '巴塞' },
  { value: 'madrid',    en: 'Madrid',    zh: '马德里',   shortEn: 'MAD', shortZh: '马德' },
  { value: 'valencia',  en: 'Valencia',  zh: '瓦伦西亚', shortEn: 'VLC', shortZh: '瓦伦' },
]

interface Props {
  city: City
  onChange: (city: City) => void
}

export default function CitySelector({ city, onChange }: Props) {
  const { lang } = useLanguage()

  return (
    <div className="flex flex-col items-center gap-2 mb-4">
      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        {lang === 'zh' ? '选择城市' : 'Analysing properties in'}
      </p>
      <div className="flex gap-1 bg-stone-100 rounded-lg p-1">
        {CITIES.map(c => (
          <button
            key={c.value}
            type="button"
            onClick={() => onChange(c.value)}
            className={`px-4 py-2 rounded-md text-sm font-semibold transition-all ${
              city === c.value
                ? 'bg-white shadow-sm text-stone-800 border border-amber-200'
                : 'text-stone-500 hover:text-stone-700'
            }`}
          >
            <span className="hidden sm:inline">{lang === 'zh' ? c.zh : c.en}</span>
            <span className="sm:hidden">{lang === 'zh' ? c.shortZh : c.shortEn}</span>
          </button>
        ))}
      </div>
      {/* City-specific tagline */}
      <p className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
        {city === 'madrid'
          ? (lang === 'zh' ? '6%印花税 · 无租金管控 · 最高9.8%回报率' : '6% ITP · No rent control · Yields up to 9.8%')
          : city === 'valencia'
          ? (lang === 'zh' ? '10%印花税 · 无租金管控 · 注意洪水风险' : '10% ITP · No rent control · Check DANA flood risk')
          : (lang === 'zh' ? '10%印花税 · 租金管控 · 2028短租禁令' : '10% ITP · Rent control · Airbnb ban 2028')
        }
      </p>
    </div>
  )
}
