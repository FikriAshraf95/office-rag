import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { configureHttp, http } from '@/api/http'
import { optionLabels } from '@/components/ui/select/testing'
import configFixture from '@/fixtures/config.json'
import { DEMO_USER_STORAGE_KEY, useUserStore } from '@/stores/user'
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
