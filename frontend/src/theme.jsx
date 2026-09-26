import { createContext, useContext, useEffect, useMemo, useState } from 'react'

export const THEMES = [
  { id: 'islands-dark', label: 'Islands Dark' },
  { id: 'islands-light', label: 'Islands Light' },
  { id: 'islands-darcula', label: 'Islands Darcula' },
  { id: 'high-contrast', label: 'High Contrast' },
  { id: 'dark', label: 'Dark' },
  { id: 'light', label: 'Light' },
  { id: 'light-light-header', label: 'Light with Light Header' },
  { id: 'darcula', label: 'Darcula' },
]

const STORAGE_KEY = 'er-ui-theme'
const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'islands-dark'
    } catch {
      return 'islands-dark'
    }
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      /* ignore */
    }
  }, [theme])

  const value = useMemo(
    () => ({
      theme,
      setTheme: setThemeState,
      themes: THEMES,
    }),
    [theme]
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return ctx
}
