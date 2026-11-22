import { describe, expect, it } from 'vitest'
import answerSse from '@/fixtures/chat-answer.sse?raw'
import { createSseParser, readEvents, type ChatEvent } from './sse'

const wire = [
  'event: meta\ndata: {"questionId":"q1"}\n\n',
  ': ping\n\n',
  'event: sources\ndata: {"sources":[]}\n\n',
  'event: delta\ndata: {"text":"Hello"}\n\n',
  'event: done\ndata: {"found":true,"cited":[],"model":"m","usage":{"promptTokens":1,"completionTokens":1},"latencyMs":1,"firstTokenMs":1}\n\n',
  'event: error\ndata: {"code":"provider_unavailable","detail":"Try again."}\n\n',
].join('')

function parseInChunks(text: string, size: number): ChatEvent[] {
  const events: ChatEvent[] = []
  const parser = createSseParser((e) => events.push(e))
  for (let i = 0; i < text.length; i += size) parser.push(text.slice(i, i + size))
  parser.flush()
  return events
}

describe('SSE reader (Spec07_Ac01)', () => {
  it('Spec07_Ac01 parses meta, sources, delta, done and error at any chunk boundary', () => {
    const whole = parseInChunks(wire, wire.length)
    expect(whole.map((e) => e.event)).toEqual(['meta', 'sources', 'delta', 'done', 'error'])
    for (const size of [1, 2, 3, 7, 16, 50]) {
      expect(parseInChunks(wire, size)).toEqual(whole)
    }
  })

  it('Spec07_Ac01 handles CRLF line endings split between chunks', () => {
    const text = wire.replace(/\n/g, '\r\n')
    expect(parseInChunks(text, 1).map((e) => e.event)).toEqual(['meta', 'sources', 'delta', 'done', 'error'])
  })

  it('Spec07_Ac01 reads a byte stream with a multi-byte character cut in half', async () => {
    const bytes = new TextEncoder().encode('event: delta\ndata: {"text":"Saya “ini”"}\n\n')
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        for (let i = 0; i < bytes.length; i += 5) controller.enqueue(bytes.slice(i, i + 5))
        controller.close()
      },
    })
    const events: ChatEvent[] = []
    await readEvents(body, (e) => events.push(e))
    expect(events).toEqual([{ event: 'delta', data: { text: 'Saya “ini”' } }])
  })

  it('Spec07_Ac01 parses the recorded answer fixture', () => {
    const events = parseInChunks(answerSse, 31)
    expect(events[0]?.event).toBe('meta')
    expect(events[1]?.event).toBe('sources')
    expect(events.at(-1)?.event).toBe('done')
  })
})
