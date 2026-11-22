import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { h } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { routes } from '@/app/router'
import type { ChatEvent } from '@/api/sse'
import { documentsApi } from '@/features/documents/api'
import { sanitizeAnswer } from '@/lib/sanitize'
import { chatApi, type Source } from './api'
import ChatPage from './ChatPage.vue'
import { renderAnswer } from './markdown'
import { useUserStore } from '@/stores/user'
import { useChatStore } from './store'

// pdf.js needs a real browser; the page it is asked to open is what matters here.
vi.mock('@/features/viewer/PdfViewer.vue', () => ({
  __esModule: true,
  default: {
    props: ['blob', 'page'],
    setup(props: { page: number }) {
      return () => h('div', { 'data-testid': 'pdf-stub', 'data-page': props.page })
    },
  },
}))

const source = (n: number, over: Partial<Source> = {}): Source => ({
  n,
  documentId: `d${n}`,
  chunkId: `c${n}`,
  title: `Doc ${n}`,
  fileType: 'md',
  headingPath: [`Doc ${n}`, 'Section'],
  section: null,
  pageStart: null,
  pageEnd: null,
  sheet: null,
  effectiveDate: '2026-01-01',
  snippet: `snippet ${n}`,
  ...over,
})

const doneEvent = (over: Record<string, unknown> = {}): ChatEvent => ({
  event: 'done',
  data: {
    found: true,
    cited: [1],
    finalText: null,
    model: 'nemo-super',
    usage: { promptTokens: 1, completionTokens: 1 },
    latencyMs: 2100,
    firstTokenMs: 500,
    ...over,
  },
})

/** Makes `chatApi.stream` emit these events, then end. */
function script(events: ChatEvent[]) {
  return vi.spyOn(chatApi, 'stream').mockImplementation(async (_q, _h, onEvent) => {
    for (const e of events) onEvent(e)
  })
}

const render = (text: string, count = 3) =>
  sanitizeAnswer(
    renderAnswer(
      text,
      Array.from({ length: count }, (_, i) => ({ n: i + 1, title: `Doc ${i + 1}` })),
    ),
  )

describe('citations and sanitizing (Spec07_Ac02)', () => {
  it('Spec07_Ac02 renders [1], [2][3] and [2, 3] as citation buttons', () => {
    const box = document.createElement('div')
    box.innerHTML = render('A [1]. B [2][3]. C [2, 3].')
    const cites = [...box.querySelectorAll('button.citation')].map((b) => b.getAttribute('data-cite'))
    expect(cites).toEqual(['1', '2', '3', '2', '3'])
    expect(box.querySelector('button')?.getAttribute('aria-label')).toBe('Source 1: Doc 1')
    expect(box.querySelector('button')?.getAttribute('type')).toBe('button')
  })

  it('Spec07_Ac02 leaves [9] with 3 sources as plain text', () => {
    const box = document.createElement('div')
    box.innerHTML = render('Not a source [9].')
    expect(box.querySelector('button')).toBeNull()
    expect(box.textContent).toContain('[9]')
  })

  it('Spec07_Ac02 keeps <script> and onerror= out of the DOM', () => {
    const box = document.createElement('div')
    box.innerHTML = render('<script>alert(1)</script> <img src=x onerror=alert(1)> **bold** [1]')
    expect(box.querySelector('script, img')).toBeNull()
    expect(box.querySelector('[onerror]')).toBeNull()
    expect(box.querySelector('strong')?.textContent).toBe('bold')
  })

  it('Spec07_Ac02 escapes a hostile source title in the aria-label', () => {
    const html = sanitizeAnswer(renderAnswer('x [1]', [{ n: 1, title: '"><img src=x onerror=alert(1)>' }]))
    const box = document.createElement('div')
    box.innerHTML = html
    expect(box.querySelector('img')).toBeNull()
    expect(box.querySelectorAll('button')).toHaveLength(1)
  })
})

describe('chat store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
    localStorage.clear()
  })

  it('Spec07_Ac04 done.finalText replaces the streamed text', async () => {
    script([
      { event: 'sources', data: { sources: [source(1)] } },
      { event: 'delta', data: { text: 'Uncited guess' } },
      doneEvent({ found: false, cited: [], finalText: 'I could not find this.', model: null }),
    ])
    const chat = useChatStore()
    await chat.send('Q?')
    await flushPromises()
    expect(chat.messages[0]?.answer).toBe('I could not find this.')
    expect(sessionStorage.getItem('rag-chat') ?? '').not.toContain('Uncited guess')
  })

  it('Spec07_Ac07 Stop aborts the request and keeps the partial answer as stopped', async () => {
    vi.spyOn(chatApi, 'stream').mockImplementation(
      (_q, _h, onEvent, signal) =>
        new Promise<void>((_resolve, reject) => {
          onEvent({ event: 'delta', data: { text: 'Partial' } })
          signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
        }),
    )
    const chat = useChatStore()
    const pending = chat.send('Q?')
    await flushPromises()
    expect(chat.streaming).toBe(true)
    chat.stop()
    await pending
    expect(chat.messages[0]).toMatchObject({ status: 'stopped', answer: 'Partial' })
    expect(chat.streaming).toBe(false)
  })

  it('Spec07_Ac07 sends only the last 4 finished turns as history', async () => {
    const stream = script([{ event: 'delta', data: { text: 'a' } }, doneEvent()])
    const chat = useChatStore()
    for (let i = 1; i <= 6; i++) await chat.send(`Q${i}`)
    const history = stream.mock.calls.at(-1)?.[1]
    expect(history?.map((t) => t.question)).toEqual(['Q2', 'Q3', 'Q4', 'Q5'])
  })

  it('Spec07_Ac07 a run aborted by New chat does not end the next one', async () => {
    let finishOld: (() => void) | null = null
    vi.spyOn(chatApi, 'stream').mockImplementationOnce(
      (_q, _h, _onEvent, signal) =>
        new Promise<void>((_resolve, reject) => {
          // The aborted run settles late, after the next question has started.
          signal?.addEventListener('abort', () => {
            finishOld = () => reject(new DOMException('Aborted', 'AbortError'))
          })
        }),
    )
    const chat = useChatStore()
    const old = chat.send('Q1?')
    await flushPromises()
    chat.clear()
    expect(chat.streaming).toBe(false)

    vi.spyOn(chatApi, 'stream').mockImplementationOnce(() => new Promise<void>(() => {}))
    void chat.send('Q2?')
    await flushPromises()
    expect(chat.messages.map((m) => m.question)).toEqual(['Q2?'])
    ;(finishOld as (() => void) | null)?.()
    await old
    expect(chat.streaming).toBe(true)
  })

  it('Spec07_Ac07 a thread stored for another demo user is not restored', async () => {
    useUserStore().setUser('aisyah')
    script([{ event: 'delta', data: { text: 'Private answer' } }, doneEvent()])
    await useChatStore().send('Q?')
    await flushPromises()
    expect(sessionStorage.getItem('rag-chat')).toContain('Private answer')

    // A fresh page load, with the user switched before the chat store exists.
    setActivePinia(createPinia())
    useUserStore().setUser('ben')
    expect(useChatStore().messages).toEqual([])
    expect(sessionStorage.getItem('rag-chat')).toBeNull()

    setActivePinia(createPinia())
    useUserStore().setUser('aisyah')
    expect(useChatStore().messages).toEqual([])
  })

  it('Spec07_Ac06 a dropped connection keeps the partial text and says it was cut off', async () => {
    vi.spyOn(chatApi, 'stream').mockImplementation(async (_q, _h, onEvent) => {
      onEvent({ event: 'delta', data: { text: 'Half an' } })
      throw new TypeError('network error')
    })
    const chat = useChatStore()
    await chat.send('Q?')
    expect(chat.messages[0]).toMatchObject({ status: 'error', cutOff: true, answer: 'Half an' })
    expect(chat.messages[0]?.error?.detail).toBe('The answer was cut off.')
  })
})

describe('chat page', () => {
  async function mountPage() {
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push('/chat')
    return mount(ChatPage, { global: { plugins: [createPinia(), router] }, attachTo: document.body })
  }
  async function ask(wrapper: Awaited<ReturnType<typeof mountPage>>, question: string) {
    await wrapper.find('textarea').setValue(question)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
  }
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
  })

  it('Spec07_Ac03 clicking a citation opens the SourcePanel; a PDF opens at pageStart', async () => {
    script([
      {
        event: 'sources',
        data: { sources: [source(1, { fileType: 'pdf', pageStart: 3, pageEnd: 3 }), source(2)] },
      },
      { event: 'delta', data: { text: 'Answer [1]' } },
      doneEvent({ cited: [1] }),
    ])
    vi.spyOn(documentsApi, 'get').mockRejectedValue(new Error('skip'))
    vi.spyOn(documentsApi, 'chunksAround').mockResolvedValue([])
    vi.spyOn(documentsApi, 'file').mockResolvedValue(new Blob(['%PDF'], { type: 'application/pdf' }))

    const wrapper = await mountPage()
    await ask(wrapper, 'How?')
    expect(wrapper.find('[data-testid="source-panel"]').exists()).toBe(false)

    await wrapper.find('button.citation').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="source-panel"]').exists()).toBe(true)
    // The viewer is an async component: give its chunk a moment to resolve.
    await vi.waitFor(() => expect(wrapper.find('[data-testid="pdf-stub"]').exists()).toBe(true))
    expect(wrapper.get('[data-testid="pdf-stub"]').attributes('data-page')).toBe('3')
    // The original is fetched through the API client as a Blob, so X-Demo-User is sent (Spec07_Ac11).
    expect(documentsApi.file).toHaveBeenCalledWith('d1')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(wrapper.find('[data-testid="source-panel"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('Spec07_Ac04 the answer is announced only on done, not per delta', async () => {
    let finish: () => void = () => {}
    vi.spyOn(chatApi, 'stream').mockImplementation(
      (_q, _h, onEvent) =>
        new Promise<void>((resolve) => {
          onEvent({ event: 'sources', data: { sources: [source(1)] } })
          onEvent({ event: 'delta', data: { text: 'Leave is **14 days** [1].' } })
          finish = () => {
            onEvent(doneEvent())
            resolve()
          }
        }),
    )
    const wrapper = await mountPage()
    await ask(wrapper, 'Leave?')
    const live = () => wrapper.get('[data-testid="answer-live"]')
    expect(wrapper.findAll('[aria-live]').map((e) => e.attributes('data-testid'))).toEqual(['answer-live'])
    expect(live().text()).toBe('')

    finish()
    await flushPromises()
    expect(live().text()).toBe('Leave is 14 days.')
    wrapper.unmount()
  })

  it('Spec07_Ac05 not found shows an info banner with the contact and no source cards', async () => {
    script([
      { event: 'sources', data: { sources: [] } },
      { event: 'delta', data: { text: 'I could not find this. Please contact HR, hr@serimaju.example.' } },
      doneEvent({ found: false, cited: [], model: null }),
    ])
    const wrapper = await mountPage()
    await ask(wrapper, 'Q30?')
    expect(wrapper.get('[data-testid="not-found"]').text()).toContain('hr@serimaju.example')
    expect(wrapper.find('[data-testid="source-cards"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('Spec07_Ac06 quota_exhausted is a warning without Retry; other errors have Retry', async () => {
    script([{ event: 'error', data: { code: 'quota_exhausted', detail: 'The plan quota is used up.' } }])
    const wrapper = await mountPage()
    await ask(wrapper, 'Q?')
    expect(wrapper.text()).toContain('The plan quota is used up.')
    expect(wrapper.text()).not.toContain('Retry')

    script([{ event: 'error', data: { code: 'provider_unavailable', detail: 'Try again shortly.' } }])
    await ask(wrapper, 'Q2?')
    expect(wrapper.text()).toContain('Try again shortly.')
    expect(wrapper.text()).toContain('Retry')
    wrapper.unmount()
  })
})
