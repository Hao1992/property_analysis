import { useState } from 'react'
import type { AnalyzeResponse, AnalyzeRequest } from './types/analysis'
import { analyzeProperty } from './api/client'
import { useLanguage } from './contexts/LanguageContext'
import AddressInput from './components/AddressInput'
import Report from './pages/Report'
import Compare from './pages/Compare'
import CostCalculator from './components/CostCalculator'

type Tab = 'analyze' | 'compare'

export default function App() {
  const { lang, setLang, t } = useLanguage()
  const [tab, setTab]         = useState<Tab>('analyze')
  const [result, setResult]   = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  const handleAnalyze = async (req: AnalyzeRequest) => {
    setLoading(true)
    setError(null)
    setProgress(0)
    const ticker = setInterval(() => {
      setProgress(p => p < 85 ? p + Math.random() * 8 : p)
    }, 800)
    try {
      const data = await analyzeProperty({ ...req, language: lang })
      setProgress(100)
      setTimeout(() => { setResult(data); setProgress(0) }, 300)
    } catch (e: unknown) {
      let msg: string = t.errors.generic
      if (e && typeof e === 'object' && 'response' in e) {
        const resp = (e as { response?: { data?: { detail?: string }, status?: number } }).response
        if (resp?.status === 429) msg = t.errors.rateLimit
        else msg = resp?.data?.detail ?? msg
      } else if (e instanceof Error) {
        msg = e.message
      }
      setError(msg)
    } finally {
      clearInterval(ticker)
      setLoading(false)
    }
  }

  const isRateLimit = error?.includes('5') || error?.includes('今天') || error?.includes('tomorrow')

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-page)' }}>

      {/* Navigation */}
      <header className="bg-white border-b sticky top-0 z-50 print:hidden" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center font-display font-bold text-white text-sm" style={{ backgroundColor: 'var(--accent)' }}>B</div>
            <div>
              <h1 className="text-base font-semibold font-display" style={{ color: 'var(--text-main)' }}>Beyond Price</h1>
              <p className="text-xs hidden sm:block" style={{ color: 'var(--text-muted)' }}>{t.nav.tagline}</p>
            </div>
          </div>

          <div className="flex gap-1 ml-4 bg-stone-100 rounded-lg p-1">
            {(['analyze', 'compare'] as Tab[]).map(tp => (
              <button
                key={tp}
                onClick={() => { setTab(tp); if (tp === 'compare') setResult(null) }}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  tab === tp ? 'bg-white shadow-sm text-stone-800' : 'text-stone-500 hover:text-stone-700'
                }`}
              >
                {tp === 'analyze' ? t.nav.analyze : t.nav.compare}
              </button>
            ))}
          </div>

          {/* Language toggle */}
          <div className="flex gap-1 bg-stone-100 rounded-lg p-1">
            {(['en', 'zh'] as const).map(l => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                  lang === l ? 'bg-white shadow-sm text-stone-800' : 'text-stone-400 hover:text-stone-600'
                }`}
              >
                {l === 'en' ? 'EN' : '中文'}
              </button>
            ))}
          </div>

          {result && tab === 'analyze' && (
            <button
              onClick={() => setResult(null)}
              className="ml-auto text-sm flex items-center gap-1 transition-colors"
              style={{ color: 'var(--accent)' }}
            >
              {t.nav.newAnalysis}
            </button>
          )}
        </div>

        {loading && (
          <div className="h-0.5 bg-stone-100">
            <div className="h-full transition-all duration-500" style={{ width: `${progress}%`, backgroundColor: 'var(--accent)' }} />
          </div>
        )}
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {tab === 'compare' && <Compare />}

        {tab === 'analyze' && !result && (
          <div className="max-w-2xl mx-auto">
            {/* Hero */}
            <div className="text-center mb-10 pt-6">
              <p className="text-xs font-medium tracking-widest uppercase mb-4" style={{ color: 'var(--accent)' }}>
                {t.hero.badge}
              </p>
              <h2 className="font-display text-4xl sm:text-5xl font-bold mb-4 leading-tight" style={{ color: 'var(--text-main)' }}>
                {t.hero.h1}<br />
                <span className="italic" style={{ color: 'var(--accent)' }}>{t.hero.h2}</span>
              </h2>
              <p className="text-lg leading-relaxed mb-2" style={{ color: 'var(--text-sub)' }}>
                {t.hero.sub}
              </p>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{t.hero.tagline}</p>

              <div className="flex items-center justify-center gap-8 mt-8 mb-2">
                {t.hero.stats.map(({ n, label }) => (
                  <div key={label} className="text-center">
                    <p className="font-display text-2xl font-bold" style={{ color: 'var(--accent)' }}>{n}</p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>
                  </div>
                ))}
              </div>
            </div>

            <AddressInput onSubmit={handleAnalyze} loading={loading} />

            {loading && (
              <div className="mt-6 card p-5 text-center space-y-2">
                <div className="flex items-center justify-center gap-3">
                  <div className="w-4 h-4 rounded-full animate-pulse" style={{ backgroundColor: 'var(--accent)' }} />
                  <p className="font-medium" style={{ color: 'var(--text-main)' }}>{t.loading.title}</p>
                </div>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{t.loading.sub}</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{t.loading.time}</p>
              </div>
            )}

            {error && (
              <div className="mt-4 disclosure-red p-4 flex gap-3">
                <span className="text-red-500 text-xl shrink-0">⚠</span>
                <div>
                  <p className="font-semibold text-red-700 text-sm">{error}</p>
                  {isRateLimit && (
                    <p className="text-xs text-red-600 mt-1">{t.errors.rateLimitSub}</p>
                  )}
                </div>
              </div>
            )}

            <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted)' }}>
              {t.hero.limit}
            </p>

            {/* Cost calculator — standalone, always visible on home */}
            {!result && !loading && (
              <div className="mt-8">
                <CostCalculator />
              </div>
            )}
          </div>
        )}

        {tab === 'analyze' && result && <Report data={result} />}
      </main>

      {!result && tab === 'analyze' && (
        <footer className="border-t mt-16 py-8 print:hidden" style={{ borderColor: 'var(--border)' }}>
          <div className="max-w-5xl mx-auto px-6 text-center">
            <p className="text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>{t.footer.brand}</p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{t.footer.data}</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{t.footer.disclaimer}</p>
          </div>
        </footer>
      )}
    </div>
  )
}
