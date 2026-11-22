import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { configureHttp, http } from '@/api/http'
import { optionLabels } from '@/components/ui/select/testing'
import { configFixture } from '@/features/config/api'
import { DEMO_USER_STORAGE_KEY, useUserStore } from '@/stores/user'
import App from './App.vue'
import AppLayout from './layouts/AppLayout.vue'
import { routes } from './router'

/** Answers `/config` with the fixture and `/me` with the chosen user; records each request's X-Demo-User. */
function fakeApi() {
  const seen: { url?: string; user: unknown }[] = []
  const original = http.defaults.adapter
  http.defaults.adapter = (config) => {
    seen.push({ url: config.url, user: config.headers.get('X-Demo-User') ?? undefined })
    const data = config.url === '/config' ? configFixture : null
    return Promise.resolve({ data, status: 200, statusText: '', headers: {}, config })
  }
  return { seen, restore: () => (http.defaults.adapter = original) }
}

async function mountShell(path = '/') {
  const pinia = createPinia()
  setActivePinia(pinia)
  const user = useUserStore()
  configureHttp({ demoUser: () => user.userId })
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push(path)
  await router.isReady()
  const wrapper = mount(
    { components: { AppLayout }, template: '<AppLayout><RouterView /></AppLayout>' },
    { global: { plugins: [pinia, router] }, attachTo: document.body },
  )
  await flushPromises()
  return { wrapper, router, user }
}

describe('app shell (SPEC-07 §3, §4, §8)', () => {
  let api: ReturnType<typeof fakeApi>
  beforeEach(() => {
    localStorage.clear()
    api = fakeApi()
  })
  afterEach(() => {
    api.restore()
    document.body.innerHTML = ''
  })

  it('Spec07_Shell renders the sidebar nav: Chat, Documents, Usage', async () => {
    const { wrapper, router } = await mountShell('/')
    const links = wrapper.get('[data-testid="main-nav"]').findAll('a')
    expect(links.map((a) => a.text())).toEqual(['Chat', 'Documents', 'Usage'])
    expect(links.map((a) => a.attributes('href'))).toEqual(['/chat', '/documents', '/usage'])
    // `/` redirects to the chat page.
    expect(router.currentRoute.value.name).toBe('chat')
    expect(wrapper.text()).toContain('Ask about company documents')
    expect(wrapper.text()).toContain('Serimaju')
    wrapper.unmount()
  })

  it('keeps Documents highlighted on a document detail page', async () => {
    const { wrapper } = await mountShell('/documents/6f1d1c52-0000-4000-8000-000000000001')
    const current = wrapper.get('[data-testid="main-nav"]').findAll('a[aria-current="page"]')
    expect(current.map((a) => a.text())).toEqual(['Documents'])
    wrapper.unmount()
  })

  it('Spec07_Ac08_DemoUser lists the demo users from GET /config, fetched without X-Demo-User', async () => {
    const { wrapper, user } = await mountShell('/documents')
    const trigger = wrapper.get('[data-testid="demo-user-select"]')
    expect(await optionLabels(trigger.element)).toEqual(['Aisyah (HR)', 'Ben (Staff)'])
    expect(api.seen[0]).toEqual({ url: '/config', user: undefined })
    // With nothing stored, the first demo user is chosen and remembered.
    expect(user.userId).toBe('aisyah')
    expect(localStorage.getItem(DEMO_USER_STORAGE_KEY)).toBe('aisyah')
    wrapper.unmount()
  })

  it('Spec07_Ac08_DemoUser keeps the stored user and sends it on later requests', async () => {
    localStorage.setItem(DEMO_USER_STORAGE_KEY, 'ben')
    const { wrapper, user } = await mountShell('/usage')
    expect(user.userId).toBe('ben')
    expect(wrapper.get('[data-testid="demo-user-select"]').text()).toContain('Ben (Staff)')
    await http.get('/me')
    expect(api.seen.at(-1)).toEqual({ url: '/me', user: 'ben' })
    wrapper.unmount()
  })

  it('shows the not-found page for an unknown path', async () => {
    const { wrapper } = await mountShell('/nowhere')
    expect(wrapper.text()).toContain('Page not found')
    wrapper.unmount()
  })
})

describe('password mode (SPEC-11 §5.2, M100)', () => {
  const passwordConfig = { ...configFixture, demoUsers: [], authMode: 'password' as const }
  const ben = { id: 'ben', name: 'Ben (Staff)', groups: ['all'], isAdmin: false }
  const aisyah = { id: 'aisyah', name: 'Aisyah (HR)', groups: ['all', 'hr'], isAdmin: true }
  let seen: { method?: string; url?: string; user: unknown; data?: unknown }[]
  let session: typeof ben | null
  let original: typeof http.defaults.adapter

  function reject(config: InternalAxiosRequestConfig, status: number, code: string) {
    const response = { data: { status, code, detail: 'No.' }, status, statusText: '', headers: {}, config }
    return Promise.reject(new AxiosError('refused', 'ERR_BAD_REQUEST', config, undefined, response))
  }

  /** A fake API with one valid password per user; `session` is who the cookie belongs to. */
  function fakePasswordApi(signedIn: typeof ben | null) {
    seen = []
    session = signedIn
    original = http.defaults.adapter
    http.defaults.adapter = (config) => {
      seen.push({
        method: config.method,
        url: config.url,
        user: config.headers.get('X-Demo-User') ?? undefined,
        data: config.data,
      })
      const ok = (data: unknown) =>
        Promise.resolve({ data, status: 200, statusText: '', headers: {}, config })
      if (config.url === '/config') return ok(passwordConfig)
      if (config.url === '/auth/login') {
        const body = JSON.parse(String(config.data)) as { username: string; password: string }
        const user = { ben, aisyah }[body.username as 'ben' | 'aisyah']
        if (!user || body.password !== `${body.username}-pw`) return reject(config, 401, 'bad_credentials')
        session = user
        return ok(user)
      }
      if (config.url === '/auth/logout') {
        session = null
        return Promise.resolve({ data: null, status: 204, statusText: '', headers: {}, config })
      }
      if (!session) return reject(config, 401, 'unknown_user')
      if (config.url === '/me') return ok(session)
      return ok(config.url === '/documents' ? { items: [] } : null)
    }
  }

  async function mountApp(path = '/chat') {
    const pinia = createPinia()
    setActivePinia(pinia)
    const user = useUserStore()
    configureHttp({
      demoUser: () => user.demoHeader,
      onSignedOut: () => {
        if (!user.isPassword) return false
        user.signedOut()
        return true
      },
    })
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push(path)
    const wrapper = mount(App, { global: { plugins: [pinia, router] }, attachTo: document.body })
    await flushPromises()
    return { wrapper, user }
  }

  async function signIn(wrapper: VueWrapper, username: string, password: string) {
    await wrapper.get('input[name="username"]').setValue(username)
    await wrapper.get('input[name="password"]').setValue(password)
    await wrapper.get('[data-testid="login-form"]').trigger('submit')
    await flushPromises()
  }

  beforeEach(() => localStorage.clear())
  afterEach(() => {
    http.defaults.adapter = original
    configureHttp({ onSignedOut: () => false })
    document.body.innerHTML = ''
  })

  it('shows the login page when there is no session, and the app after signing in', async () => {
    fakePasswordApi(null)
    const { wrapper, user } = await mountApp()
    expect(wrapper.find('[data-testid="login-form"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="top-bar"]').exists()).toBe(false)

    await signIn(wrapper, 'ben', 'wrong')
    expect(wrapper.get('[role="alert"]').text()).toContain('username or password is wrong')
    expect((wrapper.get('input[name="password"]').element as HTMLInputElement).value).toBe('')

    await signIn(wrapper, 'ben', 'ben-pw')
    expect(wrapper.find('[data-testid="login-form"]').exists()).toBe(false)
    expect(wrapper.get('[data-testid="signed-in-user"]').text()).toBe('Ben (Staff)')
    expect(user.userId).toBe('ben')
    wrapper.unmount()
  })

  it('hides the switcher and the admin pages for staff, and never sends X-Demo-User', async () => {
    fakePasswordApi(ben)
    const { wrapper, user } = await mountApp('/documents')
    expect(wrapper.find('[data-testid="demo-user-select"]').exists()).toBe(false)
    const links = wrapper.get('[data-testid="main-nav"]').findAll('a')
    expect(links.map((a) => a.text())).toEqual(['Chat', 'Documents'])
    expect(wrapper.text()).not.toContain('Drop files')
    expect(user.isAdmin).toBe(false)
    expect(seen.every((r) => r.user === undefined)).toBe(true)
    expect(localStorage.getItem(DEMO_USER_STORAGE_KEY)).toBeNull()
    wrapper.unmount()
  })

  it('shows the admin pages to an admin', async () => {
    fakePasswordApi(aisyah)
    const { wrapper } = await mountApp('/documents')
    const links = wrapper.get('[data-testid="main-nav"]').findAll('a')
    expect(links.map((a) => a.text())).toEqual(['Chat', 'Documents', 'Usage'])
    expect(wrapper.text()).toContain('Drop files')
    wrapper.unmount()
  })

  it('Sign out, or a session that expires, returns to the login page', async () => {
    fakePasswordApi(ben)
    const { wrapper } = await mountApp('/documents')
    await wrapper.get('[data-testid="sign-out"]').trigger('click')
    await flushPromises()
    expect(seen.some((r) => r.method === 'post' && r.url === '/auth/logout')).toBe(true)
    expect(wrapper.find('[data-testid="login-form"]').exists()).toBe(true)

    await signIn(wrapper, 'ben', 'ben-pw')
    session = null // the cookie expired on the server
    await expect(http.get('/me')).rejects.toBeTruthy()
    await flushPromises()
    expect(wrapper.find('[data-testid="login-form"]').exists()).toBe(true)
    wrapper.unmount()
  })
})
