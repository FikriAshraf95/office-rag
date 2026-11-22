import type { components } from '@/api/schema'
import { demoUserHeaders, type ApiProblem } from '@/api/http'

/**
 * POST + ReadableStream reader for the chat stream (SPEC-07 §2, SPEC-05 §6). Never `EventSource`:
 * it can't POST and can't send `X-Demo-User`. The parser handles events split across arbitrary
 * chunk boundaries; `: ping` keep-alive comments are ignored.
 */
type Schemas = components['schemas']

export type ChatEvent =
  | { event: 'meta'; data: Schemas['SseMeta'] }
  | { event: 'sources'; data: Schemas['SseSources'] }
  | { event: 'delta'; data: Schemas['SseDelta'] }
  | { event: 'done'; data: Schemas['SseDone'] }
  | { event: 'error'; data: Schemas['SseError'] }

const EVENT_NAMES = new Set(['meta', 'sources', 'delta', 'done', 'error'])

/** A non-2xx answer before the stream started: a normal problem response. */
export class SseHttpError extends Error {
  readonly problem: ApiProblem
  constructor(problem: ApiProblem) {
    super(problem.detail)
    this.problem = problem
  }
}

export interface SseParser {
  push(text: string): void
  /** Dispatches a final event that has no trailing blank line. */
  flush(): void
}

export function createSseParser(onEvent: (event: ChatEvent) => void): SseParser {
  let buffer = ''
  let name = 'message'
  let data: string[] = []

  function dispatch() {
    if (data.length && EVENT_NAMES.has(name)) {
      try {
        onEvent({ event: name, data: JSON.parse(data.join('\n')) } as ChatEvent)
      } catch {
        // A malformed payload is dropped; the stream carries on.
      }
    }
    name = 'message'
    data = []
  }

  function line(text: string) {
    if (text === '') return dispatch()
    if (text.startsWith(':')) return
    const colon = text.indexOf(':')
    const field = colon === -1 ? text : text.slice(0, colon)
    const value = colon === -1 ? '' : text.slice(colon + 1).replace(/^ /, '')
    if (field === 'event') name = value
    else if (field === 'data') data.push(value)
  }

  return {
    push(text) {
      buffer += text
      // A trailing CR may be the first half of CRLF: wait for the next chunk to know.
      const held = buffer.endsWith('\r') ? '\r' : ''
      const lines = buffer.slice(0, buffer.length - held.length).split(/\r\n|\n|\r/)
      // The last piece may be half a line: keep it.
      buffer = (lines.pop() ?? '') + held
      for (const l of lines) line(l)
    },
    flush() {
      const rest = buffer.replace(/\r$/, '')
      if (rest) line(rest)
      buffer = ''
      dispatch()
    },
  }
}

async function readProblem(response: Response): Promise<ApiProblem> {
  try {
    const body = (await response.json()) as Partial<ApiProblem>
    return {
      status: response.status,
      code: body.code ?? 'unknown',
      detail: body.detail ?? response.statusText,
      ...body,
    }
  } catch {
    return { status: response.status, code: 'unknown', detail: response.statusText || 'Request failed.' }
  }
}

export interface StreamOptions {
  signal?: AbortSignal
  onEvent: (event: ChatEvent) => void
}

/** Feeds a ReadableStream of bytes through the parser. */
export async function readEvents(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: ChatEvent) => void,
): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  const parser = createSseParser(onEvent)
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    parser.push(decoder.decode(value, { stream: true }))
  }
  parser.push(decoder.decode())
  parser.flush()
}

/**
 * `POST /api/v1<path>` and calls `onEvent` for each event. Resolves when the stream ends; rejects
 * with `SseHttpError` for a problem response, an `AbortError` when `signal` aborts, or the network
 * error when the connection drops.
 */
export async function postStream(path: string, payload: unknown, options: StreamOptions): Promise<void> {
  const response = await fetch(`/api/v1${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', ...demoUserHeaders() },
    body: JSON.stringify(payload),
    signal: options.signal,
  })
  if (!response.ok) throw new SseHttpError(await readProblem(response))
  if (!response.body) throw new Error('The server sent no stream.')
  await readEvents(response.body, options.onEvent)
}
