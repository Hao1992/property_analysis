import { createContext, useContext, useState, ReactNode } from 'react'
import type { Lang } from '../i18n/strings'
import strings from '../i18n/strings'

interface LangCtx {
  lang: Lang
  setLang: (l: Lang) => void
  t: typeof strings['en']
}

const LanguageContext = createContext<LangCtx>({
  lang: 'en',
  setLang: () => {},
  t: strings.en,
})

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    try { return (localStorage.getItem('bp_lang') as Lang) || 'en' } catch { return 'en' }
  })

  const setLang = (l: Lang) => {
    setLangState(l)
    try { localStorage.setItem('bp_lang', l) } catch {}
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang, t: strings[lang] as typeof strings['en'] }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  return useContext(LanguageContext)
}
