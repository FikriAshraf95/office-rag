import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { toProblem } from '@/api/http'
import { SseHttpError, type ChatEvent } from '@/api/sse'
import { useUserStore } from '@/stores/user'
import { chatApi, type Source } from './api'

/**
 * The chat thread (SPEC-07 §5.6): kept in memory and in sessionStorage (cleared by New chat). The
 * last 4 turns go as `history`. Streamed text that `done.finalText` replaces is dropped, and a
 * message that is still streaming is never persisted.
 */
export type MessageStatus = 'streaming' | 'done' | 'stopped' | 'error'

export interface ChatMessage {
  id: string
  question: string
  answer: string
  sources: Source[]
  cited: number[]
  found: boolean
  status: MessageStatus
  model: string | null
  latencyMs: number | null
  /** The user-facing problem when `status` is `error`. */
  error: { code: string; detail: string } | null
  /** The connection dropped mid-stream; the partial answer is kept. */
  cutOff: boolean
}

export const CHAT_STORAGE_KEY = 'rag-chat'
export const MAX_QUESTION_LENGTH = 1000
const HISTORY_TURNS = 4
const CUT_OFF = 'The answer was cut off.'

/**
 * The stored thread carries the demo user it belongs to. The store may be created only after the
 * user was switched on another page, so a thread saved for a different user is dropped, never shown.
 */
interface StoredThread {
  userId: string | null
  messages: ChatMessage[]
}

function readStored(userId: string | null): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(CHAT_STORAGE_KEY)
    if (!raw) return []
    const stored = JSON.parse(raw) as Partial<StoredThread>
    if (stored.userId !== userId || !Array.isArray(stored.messages)) {
      sessionStorage.removeItem(CHAT_STORAGE_KEY)
      return []
    }
    return stored.messages
  } catch {
    return []
  }
}

function writeStored(userId: string | null, messages: ChatMessage[]): void {
  try {
    const settled = messages.filter((m) => m.status !== 'streaming')
    const thread: StoredThread = { userId, messages: settled }
    if (settled.length) sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(thread))
    else sessionStorage.removeItem(CHAT_STORAGE_KEY)
  } catch {
    // Storage blocked: the thread still holds for this page.
  }
}

function blank(id: string, question: string): ChatMessage {
  return {
    id,
    question,
    answer: '',
    sources: [],
    cited: [],
    found: true,
    status: 'streaming',
    model: null,
    latencyMs: null,
    error: null,
    cutOff: false,
  }
}

export const useChatStore = defineStore('chat', () => {
  const user = useUserStore()
  const messages = ref<ChatMessage[]>(readStored(user.userId))
  const streaming = ref(false)
  let controller: AbortController | null = null

  function history(before: string): { question: string; answer: string }[] {
    const index = messages.value.findIndex((m) => m.id === before)
    return messages.value
      .slice(0, index === -1 ? undefined : index)
      .filter((m) => m.status === 'done' && m.answer)
      .slice(-HISTORY_TURNS)
      .map((m) => ({ question: m.question, answer: m.answer }))
  }

  function apply(message: ChatMessage, event: ChatEvent) {
    switch (event.event) {
      case 'sources':
        message.sources = event.data.sources
        break
      case 'delta':
        message.answer += event.data.text
        break
      case 'done':
        // finalText replaces the streamed text (SPEC-05 §4).
        if (event.data.finalText != null) message.answer = event.data.finalText
        message.found = event.data.found
        message.cited = event.data.cited
        message.model = event.data.model
        message.latencyMs = event.data.latencyMs
        message.status = 'done'
        break
      case 'error':
        message.error = event.data
        message.status = 'error'
        break
    }
  }

  async function run(id: string) {
    const message = messages.value.find((m) => m.id === id)
    if (!message) return
    Object.assign(message, blank(id, message.question))
    const own = new AbortController()
    controller = own
    streaming.value = true
    try {
      await chatApi.stream(message.question, history(id), (e) => apply(message, e), own.signal)
      // The stream ended without `done` or `error`: treat it as cut off.
      if (message.status === 'streaming') {
        message.status = 'error'
        message.cutOff = true
        message.error = { code: 'network', detail: CUT_OFF }
      }
    } catch (e) {
      if (own.signal.aborted) {
        message.status = 'stopped'
      } else if (e instanceof SseHttpError) {
        message.status = 'error'
        message.error = { code: e.problem.code, detail: e.problem.detail }
      } else {
        message.status = 'error'
        message.cutOff = message.answer !== ''
        message.error = {
          code: toProblem(e).code,
          detail: message.cutOff ? CUT_OFF : "Can't reach the server. Check your connection.",
        }
      }
    } finally {
      // Only the newest run owns the flag: a run that clear() aborted may settle after a new one
      // has started, and must not mark that one as finished.
      if (controller === own) {
        controller = null
        streaming.value = false
      }
    }
  }

  /** Sends a question; ignored while an answer streams or when empty or over the limit. */
  async function send(question: string) {
    const text = question.trim()
    if (!text || text.length > MAX_QUESTION_LENGTH || streaming.value) return
    const id = crypto.randomUUID()
    messages.value.push(blank(id, text))
    await run(id)
  }

  /** Stop: aborts the request and keeps the partial answer, marked as stopped. */
  function stop() {
    controller?.abort()
  }

  async function retry(id: string) {
    if (streaming.value) return
    await run(id)
  }

  /** New chat. */
  function clear() {
    controller?.abort()
    controller = null
    streaming.value = false
    messages.value = []
  }

  watch(messages, (value) => writeStored(user.userId, value), { deep: true })

  // Changing the demo user clears the thread (SPEC-07 §8).
  watch(
    () => user.userId,
    (next, previous) => {
      if (next !== previous) clear()
    },
  )

  return { messages, streaming, send, stop, retry, clear }
})
