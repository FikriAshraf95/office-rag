import { flushPromises, mount } from '@vue/test-utils'
import { AxiosError } from 'axios'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { routes } from '@/app/router'
import configFixture from '@/fixtures/config.json'
import documentsFixture from '@/fixtures/documents.json'
import { useUserStore } from '@/stores/user'
import { documentsApi, type Document } from './api'
import IngestStatusPill from './components/IngestStatusPill.vue'
import UploadPanel from './components/UploadPanel.vue'
import DocumentsPage from './DocumentsPage.vue'
import { POLL_INTERVAL_MS, useDocumentsStore } from './store'

const docs = documentsFixture.items as Document[]
const doc = (over: Partial<Document>): Document => ({ ...docs[0]!, ...over })

function duplicateError(existingId?: string, title?: string) {
  const detail = title ? `This file is already uploaded as "${title}".` : 'This file is already uploaded.'
  const error = new AxiosError('conflict')
  error.response = {
    status: 409,
    data: { status: 409, code: 'duplicate_document', detail, existingId },
    statusText: '',
    headers: {},
    config: {} as never,
  }
  return error
}

describe('documents list polling (Spec07_Ac08)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('Spec07_Ac08 polls every 3 s while a row is queued or processing, and stops when none is', async () => {
    const list = vi
      .spyOn(documentsApi, 'list')
      .mockResolvedValueOnce([doc({ id: 'a', ingestStatus: 'queued' })])
      .mockResolvedValueOnce([doc({ id: 'a', ingestStatus: 'processing' })])
      .mockResolvedValue([doc({ id: 'a', ingestStatus: 'ready' })])
    const store = useDocumentsStore()

    await store.load()
    expect(list).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    expect(list).toHaveBeenCalledTimes(2)
    expect(store.items[0]?.ingestStatus).toBe('processing')

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    expect(list).toHaveBeenCalledTimes(3)
    expect(store.items[0]?.ingestStatus).toBe('ready')

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * 5)
    expect(list).toHaveBeenCalledTimes(3)
  })

  it('Spec07_Ac08 does not poll a list that is already settled, and stops when the page goes away', async () => {
    const list = vi.spyOn(documentsApi, 'list').mockResolvedValue([doc({ ingestStatus: 'ready' })])
    const store = useDocumentsStore()
    await store.load()
    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * 3)
    expect(list).toHaveBeenCalledTimes(1)

    list.mockResolvedValue([doc({ ingestStatus: 'queued' })])
    await store.refresh()
    expect(list).toHaveBeenCalledTimes(2)
    store.stop()
    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * 3)
    expect(list).toHaveBeenCalledTimes(2)
  })

  it('filters by status and searches by title on the client', async () => {
    vi.spyOn(documentsApi, 'list').mockResolvedValue(docs)
    const store = useDocumentsStore()
    await store.load()
    store.stop()

    store.filter = 'failed'
    expect(store.visible.map((d) => d.title)).toEqual(['Leave policy 2024'])
    store.filter = 'superseded'
    expect(store.visible.map((d) => d.title)).toEqual(['Leave policy 2024'])
    store.filter = 'current'
    expect(store.visible).toHaveLength(2)
    store.filter = 'all'
    store.search = 'travel'
    expect(store.visible.map((d) => d.title)).toEqual(['Travel and Claims SOP'])
  })
})

describe('upload panel (Spec07_Ac09)', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })
  afterEach(() => vi.restoreAllMocks())

  async function mountPanel() {
    const user = useUserStore()
    user.config = configFixture
    user.setUser('ben')
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push('/documents')
    await router.isReady()
    const wrapper = mount(UploadPanel, { global: { plugins: [router] } })
    return { wrapper, store: useDocumentsStore() }
  }

  function choose(wrapper: ReturnType<typeof mount>, files: File[]) {
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: files, configurable: true })
    return input.trigger('change')
  }

  it('Spec07_Ac09 a duplicate shows "Already uploaded as" the existing title, with a link to it', async () => {
    vi.spyOn(documentsApi, 'upload').mockRejectedValue(duplicateError('doc-1', 'HR Employee Handbook 2026'))
    vi.spyOn(documentsApi, 'list').mockResolvedValue(docs)
    const { wrapper, store } = await mountPanel()

    await choose(wrapper, [new File(['%PDF-'], 'handbook.pdf', { type: 'application/pdf' })])
    await flushPromises()
    store.stop()

    const row = wrapper.find('[data-state="duplicate"]')
    expect(row.text()).toContain('Already uploaded as')
    const link = row.find('a')
    expect(link.text()).toBe('HR Employee Handbook 2026')
    expect(link.attributes('href')).toBe('/documents/doc-1')
  })

  it('Spec07_Ac09 a duplicate of a document the caller cannot see names nothing and links nowhere', async () => {
    vi.spyOn(documentsApi, 'upload').mockRejectedValue(duplicateError())
    const { wrapper, store } = await mountPanel()

    await choose(wrapper, [new File(['%PDF-'], 'secret.pdf', { type: 'application/pdf' })])
    await flushPromises()
    store.stop()

    const row = wrapper.find('[data-state="duplicate"]')
    expect(row.text()).toContain('Already uploaded')
    expect(row.find('a').exists()).toBe(false)
  })

  it('uploads each file in turn and sends the details to every one (title only for a single file)', async () => {
    const upload = vi.spyOn(documentsApi, 'upload').mockResolvedValue(docs[0]!)
    vi.spyOn(documentsApi, 'list').mockResolvedValue(docs)
    const { wrapper, store } = await mountPanel()

    await choose(wrapper, [
      new File(['%PDF-'], 'a.pdf', { type: 'application/pdf' }),
      new File(['%PDF-'], 'b.pdf', { type: 'application/pdf' }),
    ])
    await flushPromises()
    store.stop()

    expect(upload.mock.calls.map((c) => c[0].name)).toEqual(['a.pdf', 'b.pdf'])
    expect(upload.mock.calls[0]?.[1]).toMatchObject({ accessGroups: ['all'], title: undefined })
    expect(wrapper.findAll('[data-state="done"]')).toHaveLength(2)
  })
})

describe('IngestStatusPill', () => {
  it.each([
    ['queued', 'Queued'],
    ['processing', 'Processing'],
    ['ready', 'Ready'],
    ['failed', 'Failed'],
  ] as const)('shows %s as "%s"', (status, label) => {
    const wrapper = mount(IngestStatusPill, { props: { status } })
    expect(wrapper.text()).toContain(label)
    expect(wrapper.find('[data-testid="ingest-spinner"]').exists()).toBe(status === 'processing')
  })
})

describe('documents page and the demo user', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })
  afterEach(() => vi.restoreAllMocks())

  async function mountPage() {
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push('/documents')
    await router.isReady()
    const wrapper = mount(DocumentsPage, { global: { plugins: [router] } })
    await flushPromises()
    return wrapper
  }

  it('waits for a demo user, then loads the list, and loads it again for the next user', async () => {
    const list = vi
      .spyOn(documentsApi, 'list')
      .mockResolvedValue(docs.map((d) => ({ ...d, ingestStatus: 'ready' })))
    const user = useUserStore()
    user.config = configFixture
    const wrapper = await mountPage()
    expect(list).not.toHaveBeenCalled()

    user.setUser('aisyah')
    await flushPromises()
    expect(list).toHaveBeenCalledTimes(1)
    expect(wrapper.findAll('[data-testid="document-row"]')).toHaveLength(3)

    user.setUser('ben')
    await flushPromises()
    expect(list).toHaveBeenCalledTimes(2)
    wrapper.unmount()
  })

  it('shows the empty state, and stops polling when it goes away', async () => {
    vi.spyOn(documentsApi, 'list').mockResolvedValue([])
    const user = useUserStore()
    user.config = configFixture
    user.setUser('ben')
    const wrapper = await mountPage()
    expect(wrapper.text()).toContain('No documents yet')
    wrapper.unmount()
  })
})
