import { useEffect, useRef, useCallback } from 'react'

const SESSION_KEY = 'bp_sid'

function getSessionId(): string {
  try {
    let id = sessionStorage.getItem(SESSION_KEY)
    if (!id) {
      id = crypto.randomUUID()
      sessionStorage.setItem(SESSION_KEY, id)
    }
    return id
  } catch {
    return 'anon'
  }
}

async function fire(sessionId: string, requestId: string, event: string, data: Record<string, unknown> = {}) {
  try {
    const base = (import.meta.env.VITE_API_URL as string) || ''
    await fetch(`${base}/track`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, request_id: requestId, event, data }),
      keepalive: true,
    })
  } catch {
    // non-blocking — analytics must never break the app
  }
}

export function useReportAnalytics(requestId: string | undefined, language: string) {
  const sessionId = useRef(getSessionId())
  const viewed = useRef<Set<string>>(new Set())
  const sectionTimers = useRef<Map<string, number>>(new Map())

  // Fire analysis_complete on first mount
  useEffect(() => {
    if (!requestId) return
    fire(sessionId.current, requestId, 'report_viewed', { language })
  }, [requestId, language])

  // Track language switches
  const prevLang = useRef(language)
  useEffect(() => {
    if (!requestId || prevLang.current === language) return
    fire(sessionId.current, requestId, 'language_switch', { from: prevLang.current, to: language })
    prevLang.current = language
  }, [language, requestId])

  // IntersectionObserver — track when each section enters view + dwell time
  useEffect(() => {
    if (!requestId) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const section = entry.target.getAttribute('data-section')
          if (!section) return

          if (entry.isIntersecting) {
            sectionTimers.current.set(section, Date.now())
            if (!viewed.current.has(section)) {
              viewed.current.add(section)
              fire(sessionId.current, requestId, 'section_view', { section })
            }
          } else {
            const start = sectionTimers.current.get(section)
            if (start) {
              const dwell_ms = Date.now() - start
              sectionTimers.current.delete(section)
              if (dwell_ms > 2000) {
                fire(sessionId.current, requestId, 'section_dwell', { section, dwell_ms })
              }
            }
          }
        })
      },
      { threshold: 0.25 }
    )

    // Observe all annotated sections
    document.querySelectorAll('[data-section]').forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [requestId])

  const trackPdf = useCallback(() => {
    if (!requestId) return
    fire(sessionId.current, requestId, 'pdf_download', {})
  }, [requestId])

  const trackQuestionnaireOpen = useCallback(() => {
    if (!requestId) return
    fire(sessionId.current, requestId, 'questionnaire_open', {})
  }, [requestId])

  return { trackPdf, trackQuestionnaireOpen }
}
