import type { components } from '@/api/schema'
import { postStream, readEvents, type ChatEvent } from '@/api/sse'
import answerFixture from '@/fixtures/chat-answer.sse?raw'
import notFoundFixture from '@/fixtures/chat-not-found.sse?raw'

export type Source = components['schemas']['SseSource']
export type ChatTurn = components['schemas']['ChatTurnIn']

const useFixtures = import.meta.env.VITE_USE_FIXTURES === '1'

/** Fixtures mode: a question about salary or the CEO gets the recorded not-found answer. */
const NOT_FOUND_QUESTION = /salary|gaji|ceo|q30/i

function fixtureBody(text: string, signal?: AbortSignal): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  // Small slices that cut through events, as a real network does.
  const pieces = text.match(/[\s\S]{1,48}/g) ?? []
  let i = 0
  return new ReadableStream<Uint8Array>({
    async pull(controller) {
      await new Promise((resolve) => setTimeout(resolve, 25))
      if (signal?.aborted) return controller.error(new DOMException('Aborted', 'AbortError'))
      const piece = pieces[i++]
      if (piece === undefined) controller.close()
      else controller.enqueue(encoder.encode(piece))
    },
  })
}

export const chatApi = {
  /** `POST /chat`: streams the events in SPEC-05 §6. */
  async stream(
    question: string,
    history: ChatTurn[],
    onEvent: (event: ChatEvent) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    if (useFixtures) {
      const recorded = NOT_FOUND_QUESTION.test(question) ? notFoundFixture : answerFixture
      return readEvents(fixtureBody(recorded, signal), onEvent)
    }
    return postStream('/chat', { question, history }, { signal, onEvent })
  },
}
