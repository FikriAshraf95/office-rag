// Applies the saved theme (localStorage 'rag-theme') before first paint so the page doesn't flash
// the wrong theme (SPEC-07 §3). src/lib/theme.ts keeps the value up to date.
;(function () {
  var theme = 'system'
  try {
    theme = localStorage.getItem('rag-theme') || 'system'
  } catch {
    // Storage blocked: fall back to the system setting.
  }
  var dark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', dark)
})()
