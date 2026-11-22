import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

// Desktop sidebar rail (SPEC-07 §3, copied from Private Repo App). The user's choice is kept in localStorage; with no
// choice the rail is the default from 1024 to 1279px. Below 768px the drawer is used instead.
const KEY = 'rag.sidebar.collapsed'
const NARROW = '(min-width: 1024px) and (max-width: 1279px)'

function read(): boolean | null {
  try {
    const raw = localStorage.getItem(KEY)
    return raw === 'true' ? true : raw === 'false' ? false : null
  } catch {
    return null
  }
}

function write(value: boolean): void {
  try {
    localStorage.setItem(KEY, String(value))
  } catch {
    // Not remembered; nothing else depends on it.
  }
}

export const useSidebarStore = defineStore('sidebar', () => {
  const preference = ref<boolean | null>(read())
  const narrow = ref(false)
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    const query = window.matchMedia(NARROW)
    narrow.value = query.matches
    query.addEventListener('change', (e) => (narrow.value = e.matches))
  }

  /** True when the 56px rail is showing (desktop only; the drawer ignores it). */
  const rail = computed(() => preference.value ?? narrow.value)

  function toggle() {
    preference.value = !rail.value
    write(preference.value)
  }

  return { rail, toggle }
})
