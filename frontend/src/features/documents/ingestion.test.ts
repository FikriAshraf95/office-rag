import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import documentsFixture from '@/fixtures/documents.json'
import { documentsApi, type Chunk, type Document } from './api'
import ChunksTab from './components/ChunksTab.vue'
import { POLL_INTERVAL_MS, useDocumentsStore } from './store'

// M02 additions to SPEC-07 §6: re-ingest, the failed banner's Retry and the Chunks tab.
const docs = documentsFixture.items as Document[]
const doc = (over: Partial<Document>): Document => ({ ...docs[0]!, ...over })

const chunk = (n: number, over: Partial<Chunk> = {}): Chunk => ({
  id: `c${n}`,
  ordinal: n,
  chunkType: 'text',
  text: `<b>body ${n}</b>`,
  headingPath: ['Handbook', `Section ${n}`],
  section: String(n),
  pageStart: 2,
  pageEnd: 3,
  sheet: null,
  tokenCount: 120,
  ...over,
})

describe('re-ingest', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('shows the row as queued at once and polls until it settles', async () => {
    vi.spyOn(documentsApi, 'list')
      .mockResolvedValueOnce([doc({ id: 'a', ingestStatus: 'failed' })])
      .mockResolvedValue([doc({ id: 'a', ingestStatus: 'ready' })])
    const reingest = vi
      .spyOn(documentsApi, 'reingest')
      .mockResolvedValue(doc({ id: 'a', ingestStatus: 'queued' }))
    const store = useDocumentsStore()
    await store.load()

    await store.reingest('a')
    expect(reingest).toHaveBeenCalledWith('a')
    expect(store.items[0]?.ingestStatus).toBe('queued')

    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
    expect(store.items[0]?.ingestStatus).toBe('ready')
    store.stop()
  })
})

describe('chunks tab', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lists chunks with heading path, pages and tokens, and shows the text as plain text when expanded', async () => {
    vi.spyOn(documentsApi, 'chunks').mockResolvedValue({ items: [chunk(0), chunk(1)], total: 2 })
    const wrapper = mount(ChunksTab, { props: { documentId: 'a', chunkCount: 2, version: 0 } })
    await flushPromises()

    expect(wrapper.text()).toContain('2 chunks')
    expect(wrapper.text()).toContain('Handbook › Section 0')
    expect(wrapper.text()).toContain('Pages 2–3')
    expect(wrapper.text()).toContain('120 tokens')

    await wrapper.findAll('button')[0]!.trigger('click')
    expect(wrapper.find('pre').text()).toBe('<b>body 0</b>')
    expect(wrapper.find('pre b').exists()).toBe(false)
  })

  it('names the sheet instead of pages for spreadsheets', async () => {
    vi.spyOn(documentsApi, 'chunks').mockResolvedValue({
      items: [
        chunk(0, { sheet: 'Annual Leave 2026', pageStart: null, pageEnd: null, chunkType: 'table_rows' }),
      ],
      total: 1,
    })
    const wrapper = mount(ChunksTab, { props: { documentId: 'a', chunkCount: 1, version: 0 } })
    await flushPromises()
    expect(wrapper.text()).toContain('Sheet Annual Leave 2026')
  })

  it('shows an empty state before ingestion has produced chunks, and loads more on request', async () => {
    const spy = vi.spyOn(documentsApi, 'chunks').mockResolvedValue({ items: [], total: 0 })
    const empty = mount(ChunksTab, { props: { documentId: 'a', chunkCount: 0, version: 0 } })
    await flushPromises()
    expect(empty.text()).toContain('No chunks yet')

    spy.mockReset()
    spy
      .mockResolvedValueOnce({ items: [chunk(0)], total: 2 })
      .mockResolvedValueOnce({ items: [chunk(1)], total: 2 })
    const paged = mount(ChunksTab, { props: { documentId: 'b', chunkCount: 2, version: 0 } })
    await flushPromises()
    await paged
      .findAll('button')
      .find((b) => b.text() === 'Show more')!
      .trigger('click')
    await flushPromises()
    expect(spy).toHaveBeenLastCalledWith('b', 1, 50)
    expect(paged.text()).toContain('Section 1')
  })
})
