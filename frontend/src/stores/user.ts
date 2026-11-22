import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { toProblem } from '@/api/http'
import { configApi, type ConfigOut, type DemoUserOut } from '@/features/config/api'

/**
 * The demo identity (SPEC-07 §8). The chosen user id is kept in localStorage and read by
 * `http.ts` for the `X-Demo-User` header. `GET /config` loads the user list (and the rest of the
 * UI config) before a user is chosen. Other stores watch `userId` to reset on a change.
 */
export const DEMO_USER_STORAGE_KEY = 'rag-demo-user'

function readStored(): string | null {
  try {
    return localStorage.getItem(DEMO_USER_STORAGE_KEY)
  } catch {
    return null
  }
}

function writeStored(id: string | null): void {
  try {
    if (id) localStorage.setItem(DEMO_USER_STORAGE_KEY, id)
    else localStorage.removeItem(DEMO_USER_STORAGE_KEY)
  } catch {
    // Storage blocked: the choice still holds for this page.
  }
}

export const useUserStore = defineStore('user', () => {
  const userId = ref<string | null>(readStored())
  const config = ref<ConfigOut | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const demoUsers = computed<DemoUserOut[]>(() => config.value?.demoUsers ?? [])
  const current = computed(() => demoUsers.value.find((u) => u.id === userId.value) ?? null)
  const orgName = computed(() => config.value?.orgName ?? 'Company docs')

  function setUser(id: string | null) {
    userId.value = id
    writeStored(id)
  }

  /** Loads `/config`; keeps the stored user when it still exists, otherwise picks the first one. */
  async function load() {
    loading.value = true
    error.value = null
    try {
      config.value = await configApi.get()
      const users = config.value.demoUsers
      if (!users.some((u) => u.id === userId.value)) setUser(users[0]?.id ?? null)
    } catch (e) {
      error.value = toProblem(e).detail
    } finally {
      loading.value = false
    }
  }

  return { userId, config, loading, error, demoUsers, current, orgName, setUser, load }
})
