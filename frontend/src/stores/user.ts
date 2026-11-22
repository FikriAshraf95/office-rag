import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { toProblem } from '@/api/http'
import { authApi, configApi, type ConfigOut, type DemoUserOut, type MeOut } from '@/features/config/api'

/**
 * Who is using the app (SPEC-07 §8). `GET /config` runs first and says which auth mode the API uses.
 * - Demo mode: the chosen demo user id is kept in localStorage and read by `http.ts` for the
 *   `X-Demo-User` header. Every demo user is an admin.
 * - Password mode (M100): the user signs in on the login page; the API keeps an HttpOnly session
 *   cookie, and `GET /me` gives the user, groups and admin flag. No `X-Demo-User` is sent.
 * Other stores watch `userId` to load or reset on a change.
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
  const me = ref<MeOut | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isPassword = computed(() => config.value?.authMode === 'password')
  /** Password mode with no session: the app shows the login page instead of the shell. */
  const needsLogin = computed(() => isPassword.value && !me.value && !loading.value && !error.value)
  const demoUsers = computed<DemoUserOut[]>(() => config.value?.demoUsers ?? [])
  const current = computed<DemoUserOut | null>(() =>
    isPassword.value ? me.value : (demoUsers.value.find((u) => u.id === userId.value) ?? null),
  )
  /** Hides admin actions; the API enforces the same rule (403 `admin_only`). */
  const isAdmin = computed(() => (isPassword.value ? (me.value?.isAdmin ?? false) : true))
  /** The `X-Demo-User` value: demo mode only. */
  const demoHeader = computed(() => (isPassword.value ? null : userId.value))
  const orgName = computed(() => config.value?.orgName ?? 'Company docs')

  function setUser(id: string | null) {
    userId.value = id
    writeStored(id)
  }

  function signedIn(user: MeOut) {
    me.value = user
    userId.value = user.id
  }

  /** The session ended (logout, expiry, or a 401 from any call): back to the login page. */
  function signedOut() {
    me.value = null
    userId.value = null
  }

  async function loadSessionUser() {
    try {
      signedIn(await configApi.me({ silent: true }))
    } catch (e) {
      const problem = toProblem(e)
      if (problem.status === 401) signedOut()
      else error.value = problem.detail
    }
  }

  let pending: Promise<void> | null = null

  /** Loads `/config` (once at a time). Demo mode keeps the stored user when it still exists, otherwise
   * picks the first one; password mode asks `/me` whether a session exists. */
  function load(): Promise<void> {
    pending ??= (async () => {
      loading.value = true
      error.value = null
      try {
        config.value = await configApi.get()
        if (isPassword.value) {
          await loadSessionUser()
        } else {
          const users = config.value.demoUsers
          if (!users.some((u) => u.id === userId.value)) setUser(users[0]?.id ?? null)
        }
      } catch (e) {
        error.value = toProblem(e).detail
      } finally {
        loading.value = false
        pending = null
      }
    })()
    return pending
  }

  /** Throws the API error (401 `bad_credentials`, 429) for the login page to show. */
  async function login(username: string, password: string) {
    signedIn(await authApi.login(username, password))
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      signedOut()
    }
  }

  return {
    userId,
    config,
    me,
    loading,
    error,
    isPassword,
    needsLogin,
    demoUsers,
    current,
    isAdmin,
    demoHeader,
    orgName,
    setUser,
    signedOut,
    load,
    login,
    logout,
  }
})
