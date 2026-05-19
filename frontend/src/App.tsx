import { useState } from 'react'
import type { AnalyzeResponse, AnalyzeRequest } from './types/analysis'
import { analyzeProperty } from './api/client'
import AddressInput from './components/AddressInput'
import Report from './pages/Report'
import Compare from './pages/Compare'

type Tab = 'analyze' | 'compare'

export default function App() {
  const [tab, setTab]       = useState<Tab>('analyze')
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  const handleAnalyze = async (req: AnalyzeRequest) => {
    setLoading(true)
    setError(null)
    setProgress(0)

    // Simulated progress while waiting for analysis
    const ticker = setInterval(() => {
      setProgress(p => p < 85 ? p + Math.random() * 8 : p)
    }, 800)

    try {
      const data = await analyzeProperty(req)
      setProgress(100)
      setTimeout(() => { setResult(data); setProgress(0) }, 300)
    } catch (e: unknown) {
      let msg = 'Analysis failed. Please try again.'
      if (e && typeof e === 'object' && 'response' in e) {
        const resp = (e as { response?: { data?: { detail?: string }, status?: number } }).response
        if (resp?.status === 429) {
          msg = 'You have used all 5 free analyses for today. Come back tomorrow for more.'
        } else {
          msg = resp?.data?.detail ?? msg
        }
      } else if (e instanceof Error) {
        msg = e.message
      }
      setError(msg)
    } finally {
      clearInterval(ticker)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-page)' }}>

      {/* Navigation */}
      <header className="bg-white border-b sticky top-0 z-50" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center font-display font-bold text-white text-sm" style={{ backgroundColor: 'var(--accent)' }}>B</div>
            <div>
              <h1 className="text-base font-semibold font-display" style={{ color: 'var(--text-main)' }}>Beyond Price</h1>
              <p className="text-xs hidden sm:block" style={{ color: 'var(--text-muted)' }}>Barcelona · Know before you buy</p>
            </div>
          </div>

          {/* Tab bar */}
          <div className="flex gap-1 ml-4 bg-stone-100 rounded-lg p-1">
            {(['analyze', 'compare'] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => { setTab(t); if (t === 'compare') setResult(null) }}
                className={`px-3 py-1.5 rounded-md text-sm font-medium capitalize transition-all ${
                  tab === t
                    ? 'bg-white shadow-sm text-stone-800'
                    : 'text-stone-500 hover:text-stone-700'
                }`}
              >
                {t === 'analyze' ? 'Analyse' : 'Compare'}
              </button>
            ))}
          </div>

          {result && tab === 'analyze' && (
            <button
              onClick={() => setResult(null)}
              className="ml-auto text-sm flex items-center gap-1 transition-colors"
              style={{ color: 'var(--accent)' }}
            >
              <span>←</span> New analysis
            </button>
          )}
        </div>

        {/* Progress bar */}
        {loading && (
          <div className="h-0.5 bg-stone-100">
            <div
              className="h-full transition-all duration-500"
              style={{ width: `${progress}%`, backgroundColor: 'var(--accent)' }}
            />
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
                Barcelona · Free Beta
              </p>
              <h2 className="font-display text-4xl sm:text-5xl font-bold mb-4 leading-tight" style={{ color: 'var(--text-main)' }}>
                Beyond the price tag.<br />
                <span className="italic" style={{ color: 'var(--accent)' }}>Know before you buy.</span>
              </h2>
              <p className="text-lg leading-relaxed mb-2" style={{ color: 'var(--text-sub)' }}>
                Enter any Barcelona address. Get the full picture — hidden costs,
                structural risks, noise, Airbnb pressure, fair value — in 60 seconds.
              </p>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                What estate agents don't tell you. What portals can't show you.
              </p>

              {/* Trust stats */}
              <div className="flex items-center justify-center gap-8 mt-8 mb-2">
                {[
                  { n: '8', label: 'Data sources' },
                  { n: '12+', label: 'Risk factors' },
                  { n: '60s', label: 'Per report' },
                  { n: '100%', label: 'Free to try' },
                ].map(({ n, label }) => (
                  <div key={label} className="text-center">
                    <p className="font-display text-2xl font-bold" style={{ color: 'var(--accent)' }}>{n}</p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>
                  </div>
                ))}
              </div>
            </div>

            <AddressInput onSubmit={handleAnalyze} loading={loading} />

            {/* Loading state */}
            {loading && (
              <div className="mt-6 card p-5 text-center space-y-2">
                <div className="flex items-center justify-center gap-3">
                  <div className="w-4 h-4 rounded-full animate-pulse" style={{ backgroundColor: 'var(--accent)' }} />
                  <p className="font-medium" style={{ color: 'var(--text-main)' }}>Analysing property…</p>
                </div>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  Checking Catastro, Airbnb data, OSM, safety indices, school quality…
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Usually takes 30–60 seconds</p>
              </div>
            )}

            {error && (
              <div className="mt-4 disclosure-red p-4 flex gap-3">
                <span className="text-red-500 text-xl shrink-0">⚠</span>
                <div>
                  <p className="font-semibold text-red-700 text-sm">{error}</p>
                  {error.includes('5 free') && (
                    <p className="text-xs text-red-600 mt-1">Each address uses one of your 5 daily free analyses.</p>
                  )}
                </div>
              </div>
            )}

            <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted)' }}>
              5 free analyses per day · No account required · Barcelona addresses only
            </p>
          </div>
        )}

        {tab === 'analyze' && result && <Report data={result} />}
      </main>

      {/* Footer */}
      {!result && tab === 'analyze' && (
        <footer className="border-t mt-16 py-8" style={{ borderColor: 'var(--border)' }}>
          <div className="max-w-5xl mx-auto px-6 text-center">
            <p className="text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>Beyond Price — Barcelona Property Intelligence</p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Data: Catastro · INE · OpenStreetMap · Inside Airbnb · Open Data BCN · AI: Claude
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
              For informational purposes only. Not a substitute for professional legal or financial advice.
            </p>
          </div>
        </footer>
      )}
    </div>
  )
}
