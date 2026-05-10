import { useState } from 'react'
import type { AnalyzeResponse, AnalyzeRequest } from './types/analysis'
import { analyzeProperty } from './api/client'
import AddressInput from './components/AddressInput'
import Report from './pages/Report'
import Compare from './pages/Compare'

type Tab = 'analyze' | 'compare'

export default function App() {
  const [tab, setTab] = useState<Tab>('analyze')
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async (req: AnalyzeRequest) => {
    setLoading(true)
    setError(null)
    try {
      const data = await analyzeProperty(req)
      setResult(data)
    } catch (e: unknown) {
      let msg = 'Analysis failed. Please try again.'
      if (e && typeof e === 'object' && 'response' in e) {
        const resp = (e as { response?: { data?: { detail?: string } } }).response
        msg = resp?.data?.detail ?? msg
      } else if (e instanceof Error) {
        msg = e.message
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-4">
          <div>
            <h1 className="text-lg font-bold text-white">Property Analyzer</h1>
            <p className="text-xs text-slate-400">Barcelona property intelligence</p>
          </div>

          {/* Tab bar */}
          <div className="flex gap-1 ml-6 bg-slate-700 rounded-lg p-1">
            {(['analyze', 'compare'] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => { setTab(t); if (t === 'compare') setResult(null) }}
                className={`px-3 py-1 rounded-md text-sm font-medium capitalize transition-colors ${
                  tab === t ? 'bg-slate-900 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {result && tab === 'analyze' && (
            <button
              onClick={() => setResult(null)}
              className="ml-auto text-sm text-indigo-400 hover:text-indigo-300"
            >
              ← New analysis
            </button>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {tab === 'compare' && <Compare />}

        {tab === 'analyze' && !result && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold text-white mb-3">
                Know before you buy
              </h2>
              <p className="text-slate-400 text-lg">
                Enter any Barcelona address for a complete analysis — AI verdict, hidden costs,
                tourist pressure, school quality, and a fair value estimate.
              </p>
            </div>
            <AddressInput onSubmit={handleAnalyze} loading={loading} />
            {error && (
              <div className="mt-4 p-4 bg-red-900/30 border border-red-700 rounded-xl text-red-400 text-sm">
                {error}
              </div>
            )}
          </div>
        )}

        {tab === 'analyze' && result && <Report data={result} />}
      </main>
    </div>
  )
}
