import { useEffect, useState } from 'react'
import { KEYS, readJson, writeJson } from '../lib/storage'

export type Theme = 'light' | 'dark'

function systemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/** F8: predvolene podľa systému, ručná voľba sa zapamätá. */
export function useTheme(): [Theme, () => void] {
  const [chosen, setChosen] = useState<Theme | null>(() => readJson<Theme>(KEYS.theme))
  const [system, setSystem] = useState<Theme>(systemTheme)
  const theme = chosen ?? system

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => setSystem(systemTheme())
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const toggle = () => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    setChosen(next)
    writeJson(KEYS.theme, next)
  }
  return [theme, toggle]
}
