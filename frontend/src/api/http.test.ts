import { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  applyFieldErrors,
  configureHttp,
  createHttp,
  latestSignal,
  REQUEST_TIMEOUT_MS,
  resetHttpState,
  TOO_LARGE_MESSAGE,
  toProblem,
} from './http'

/** An adapter that answers every request with the given status and problem body. */
function respond(status: number, data: unknown = {}): AxiosAdapter {
  return (config: InternalAxiosRequestConfig) =>
    Promise.reject(
      new AxiosError('failed', String(status), config, null, {
        status,
        statusText: '',
        data,
        headers: {},
        config,
      }),
    )
}

function setup(status: number, data: unknown = {}) {
  const hooks = { demoUser: () => 'ben', toastError: vi.fn() }
  configureHttp(hooks)
  const http = createHttp()
  http.defaults.adapter = respond(status, data)
  return { http, hooks }
}

/** An instance that records the X-Demo-User header of every request and answers 200. */
function recording() {
  const seen: { url?: string; user: unknown }[] = []
  const http = createHttp()
  http.defaults.adapter = (config) => {
    seen.push({ url: config.url, user: config.headers.get('X-Demo-User') ?? undefined })
    return Promise.resolve({ data: null, status: 200, statusText: '', headers: {}, config })
  }
  return { http, seen }
}

const problem = (status: number, code: string, detail = 'Detail.') => ({
  status,
  code,
  detail,
  traceId: 'trace-1',
})

describe('demo identity (SPEC-07 §8)', () => {
  it('sends X-Demo-User on every request except GET /config', async () => {
    configureHttp({ demoUser: () => 'aisyah' })
    const { http, seen } = recording()
    await http.get('/config')
    await http.get('/me')
    await http.post('/documents', {})
    expect(seen).toEqual([
      { url: '/config', user: undefined },
      { url: '/me', user: 'aisyah' },
      { url: '/documents', user: 'aisyah' },
    ])
  })

  it('sends no header before a user is chosen', async () => {
    configureHttp({ demoUser: () => null })
    const { http, seen } = recording()
    await http.get('/me')
    expect(seen[0]?.user).toBeUndefined()
  })

  it('uses the API base path and no cookies or XSRF', () => {
    const http = createHttp()
    expect(http.defaults.baseURL).toBe('/api/v1')
    expect(http.defaults.withCredentials).toBeFalsy()
  })
})

describe('http error table (SPEC-08 §2)', () => {
  beforeEach(() => resetHttpState())

  it("reads a download's problem out of its Blob, so the server's words reach the toast", async () => {
    const body = new Blob([JSON.stringify(problem(409, 'ingest_in_progress', 'Wait for ingestion.'))], {
      type: 'application/problem+json',
    })
    const { http, hooks } = setup(409, body)
    const error = await http.get('/x', { responseType: 'blob' }).catch((e: unknown) => e)
    expect(hooks.toastError).toHaveBeenCalledWith('Wait for ingestion.')
    expect(toProblem(error).code).toBe('ingest_in_progress')
  })

  it("says so when a proxy refuses an upload, whose answer isn't a problem", async () => {
    const { http, hooks } = setup(413, '<html>Request Entity Too Large</html>')
    await http.post('/x', {}).catch(() => undefined)
    expect(hooks.toastError).toHaveBeenCalledWith(TOO_LARGE_MESSAGE)
  })

  it('shows any other status too, but leaves 404 to the page', async () => {
    const quota = setup(503, problem(503, 'quota_exhausted', 'The AI quota is used up.'))
    await quota.http.get('/x').catch(() => undefined)
    expect(quota.hooks.toastError).toHaveBeenCalledWith('The AI quota is used up.')
    const missing = setup(404, problem(404, 'not_found'))
    await missing.http.get('/x').catch(() => undefined)
    expect(missing.hooks.toastError).not.toHaveBeenCalled()
  })

  it('times out ordinary calls, but never an upload or a download', async () => {
    const timeouts: (number | undefined)[] = []
    const http = createHttp()
    http.defaults.adapter = (config) => {
      timeouts.push(config.timeout)
      return Promise.resolve({ data: null, status: 200, statusText: '', headers: {}, config })
    }
    await http.get('/x')
    await http.post('/x', new FormData())
    await http.get('/x', { responseType: 'blob' })
    expect(timeouts).toEqual([REQUEST_TIMEOUT_MS, 0, 0])
  })

  it('409 duplicate_document keeps existingId for the page', async () => {
    const { http, hooks } = setup(409, {
      ...problem(409, 'duplicate_document', 'Already uploaded.'),
      existingId: 'd1',
    })
    const error = await http.post('/x', {}).catch((e: unknown) => e)
    expect(hooks.toastError).toHaveBeenCalledWith('Already uploaded.')
    expect(toProblem(error).existingId).toBe('d1')
  })

  it('422 validation_failed is left to the form; other 422s are toasted', async () => {
    const validation = setup(422, { ...problem(422, 'validation_failed'), errors: { title: ['Required.'] } })
    await expect(validation.http.post('/x', {})).rejects.toThrow()
    expect(validation.hooks.toastError).not.toHaveBeenCalled()

    const tooLong = setup(422, problem(422, 'query_too_long', 'Shorten the question.'))
    await expect(tooLong.http.post('/x', {})).rejects.toThrow()
    expect(tooLong.hooks.toastError).toHaveBeenCalledWith('Shorten the question.')
  })

  it('500 toasts the trace reference', async () => {
    const { http, hooks } = setup(500, problem(500, 'internal'))
    await expect(http.get('/x')).rejects.toThrow()
    expect(hooks.toastError).toHaveBeenCalledWith('Something went wrong. Reference: trace-1')
  })

  it('silent requests never toast', async () => {
    const { http, hooks } = setup(409, problem(409, 'x'))
    await expect(http.get('/x', { silent: true })).rejects.toThrow()
    expect(hooks.toastError).not.toHaveBeenCalled()
  })

  it('maps validation errors onto form fields', async () => {
    const { http } = setup(422, { ...problem(422, 'validation_failed'), errors: { docType: ['Bad type.'] } })
    const error = await http.post('/x', {}).catch((e: unknown) => e)
    const setErrors = vi.fn()
    expect(applyFieldErrors(error, setErrors)).toBe(true)
    expect(setErrors).toHaveBeenCalledWith({ docType: 'Bad type.' })
  })
})

describe('request helpers', () => {
  it('latestSignal aborts the previous request with the same key only', () => {
    const first = latestSignal('search')
    const other = latestSignal('filters')
    const second = latestSignal('search')
    expect(first.aborted).toBe(true)
    expect(second.aborted).toBe(false)
    expect(other.aborted).toBe(false)
  })

  it('a network failure becomes a status-0 problem', () => {
    const p = toProblem(new AxiosError('Network Error', 'ERR_NETWORK'))
    expect(p.status).toBe(0)
    expect(p.code).toBe('network')
  })
})
