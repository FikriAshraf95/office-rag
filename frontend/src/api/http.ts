import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

/**
 * The API client (SPEC-07 §3), copied from Private Repo App and trimmed for the RAG demo:
 * - base `/api/v1`, no cookies, no XSRF, no 401/403 redirect flows;
 * - every request sends `X-Demo-User` (SPEC-09 §3), except `GET /config`, which runs before a user
 *   is chosen (SPEC-07 §8);
 * - one error table for every call (below); pages only handle what is specific to them;
 * - `latestSignal(key)` aborts the previous in-flight request with the same key (search, filters).
 *
 * The demo user and toasts are wired in by `configureHttp` at boot, which keeps this module free of
 * import cycles and easy to test.
 */

declare module 'axios' {
  interface AxiosRequestConfig {
    /** Don't toast; the caller shows its own message. */
    silent?: boolean
  }
}

/** The problem+json shape every API error uses (SPEC-08 §2). Extra members vary per code. */
export interface ApiProblem {
  status: number
  code: string
  title?: string
  detail: string
  errors?: Record<string, string[]>
  traceId?: string
  /** `duplicate_document` only, and only when the caller can see the existing document. */
  existingId?: string
}

export interface HttpHooks {
  /** The chosen demo user's id, sent as `X-Demo-User`; null before one is chosen. */
  demoUser: () => string | null
  toastError: (message: string) => void
}

export const DEMO_USER_HEADER = 'X-Demo-User'

let hooks: HttpHooks = {
  demoUser: () => null,
  toastError: () => {},
}

export function configureHttp(next: Partial<HttpHooks>): void {
  hooks = { ...hooks, ...next }
}

/** The `X-Demo-User` header for the current user, for callers outside axios (sse.ts). */
export function demoUserHeaders(): Record<string, string> {
  const user = hooks.demoUser()
  return user ? { [DEMO_USER_HEADER]: user } : {}
}

export const TOO_LARGE_MESSAGE = 'This file is too large to upload.'
/** No answer by then means a hung connection. Uploads and downloads are as long as the file needs. */
export const REQUEST_TIMEOUT_MS = 120_000

/** For tests: forget pending latestSignal requests. */
export function resetHttpState(): void {
  pending.clear()
}

/** `GET /config` is the one /api/v1 call made without `X-Demo-User` (SPEC-07 §8). */
function isPublic(config: InternalAxiosRequestConfig): boolean {
  const method = (config.method ?? 'get').toLowerCase()
  const path = (config.url ?? '').split('?')[0]?.replace(/\/+$/, '')
  return method === 'get' && path === '/config'
}

export function createHttp(): AxiosInstance {
  const instance = axios.create({
    baseURL: '/api/v1',
    headers: { Accept: 'application/json' },
    timeout: REQUEST_TIMEOUT_MS,
  })
  instance.interceptors.request.use((config) => {
    if (config.data instanceof FormData || config.responseType === 'blob') config.timeout = 0
    if (!isPublic(config)) {
      const user = hooks.demoUser()
      if (user) config.headers.set(DEMO_USER_HEADER, user)
    }
    return config
  })
  instance.interceptors.response.use((r) => r, handleError)
  return instance
}

export const http = createHttp()

/** Reads the problem out of an axios error; network failures become a 0-status problem. */
export function toProblem(error: unknown): ApiProblem {
  if (error instanceof AxiosError) {
    const data = error.response?.data as Partial<ApiProblem> | undefined
    const status = error.response?.status ?? 0
    return {
      status,
      code: data?.code ?? (status === 0 ? 'network' : 'unknown'),
      title: data?.title,
      detail:
        data?.detail ?? (status === 0 ? "Can't reach the server. Check your connection." : error.message),
      errors: data?.errors,
      traceId: data?.traceId,
      existingId: data?.existingId,
    }
  }
  return { status: 0, code: 'unknown', detail: error instanceof Error ? error.message : String(error) }
}

export function isProblem(error: unknown, status: number, code?: string): boolean {
  const p = toProblem(error)
  return p.status === status && (code === undefined || p.code === code)
}

/** A download's error arrives as a Blob too: read the problem out, so everything below can see it. */
async function readBlobProblem(blob: Blob): Promise<unknown> {
  try {
    return JSON.parse(await blob.text())
  } catch {
    return undefined
  }
}

async function handleError(error: unknown): Promise<never> {
  if (axios.isCancel(error) || !(error instanceof AxiosError)) throw error
  if (error.response?.data instanceof Blob) error.response.data = await readBlobProblem(error.response.data)
  const config = (error.config ?? {}) as InternalAxiosRequestConfig
  const problem = toProblem(error)
  const toast = (message: string) => {
    if (!config.silent) hooks.toastError(message)
  }

  // The error table (SPEC-08 §2).
  switch (problem.status) {
    case 404:
      // The page decides: a document route shows its not-found state.
      break
    case 413:
      // A proxy may answer this one itself, with no problem body.
      toast(TOO_LARGE_MESSAGE)
      break
    case 422:
      // Field errors map onto form fields (applyFieldErrors); other 422s are toasted.
      if (problem.code !== 'validation_failed') toast(problem.detail)
      break
    case 500:
      // `detail` is generic; the details are in the server logs under the trace id.
      toast(`Something went wrong. Reference: ${problem.traceId ?? 'unknown'}`)
      break
    default:
      // 400, 401 unknown_user, 409, 415, 429 and the 503 provider codes carry a user-facing detail.
      toast(problem.detail)
  }
  throw error
}

/** Maps a 422 `validation_failed` problem onto form fields. Returns true when it did. */
export function applyFieldErrors(
  error: unknown,
  setErrors: (errors: Record<string, string>) => void,
): boolean {
  const problem = toProblem(error)
  if (problem.status !== 422 || problem.code !== 'validation_failed' || !problem.errors) return false
  setErrors(
    Object.fromEntries(Object.entries(problem.errors).map(([field, messages]) => [field, messages[0] ?? ''])),
  )
  return true
}

const pending = new Map<string, AbortController>()

/**
 * An AbortSignal for `key` that cancels the previous request made with the same key, so the
 * latest search wins and a slow older answer can't overwrite it.
 */
export function latestSignal(key: string): AbortSignal {
  pending.get(key)?.abort()
  const controller = new AbortController()
  pending.set(key, controller)
  return controller.signal
}
