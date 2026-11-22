/**
 * Light, dark and system themes (SPEC-07 §3). The choice is stored in localStorage ('rag-theme')
 * so public/theme-init.js can apply it before first paint.
 */
export type ThemeChoice = 'light' | 'dark' | 'system'

export const THEME_STORAGE_KEY = 'rag-theme'

export function isThemeChoice(value: unknown): value is ThemeChoice {
  return value === 'light' || value === 'dark' || value === 'system'
}

export function readStoredTheme(): ThemeChoice {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY)
    return isThemeChoice(value) ? value : 'system'
  } catch {
    return 'system'
  }
}

function prefersDark(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches
}

/** Applies the theme to <html> and remembers it for the next load. */
export function applyTheme(choice: ThemeChoice): void {
  const dark = choice === 'dark' || (choice === 'system' && prefersDark())
  document.documentElement.classList.toggle('dark', dark)
  try {
    localStorage.setItem(THEME_STORAGE_KEY, choice)
  } catch {
    // Storage blocked: the theme still applies for this page.
  }
}

/** Re-applies "system" when the OS switches between light and dark. */
export function watchSystemTheme(current: () => ThemeChoice): void {
  if (typeof window.matchMedia !== 'function') return
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (current() === 'system') applyTheme('system')
  })
}
