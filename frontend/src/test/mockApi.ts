import { vi } from 'vitest'
import calcDefault from './fixtures/calc-default.json'

export interface MockCall {
  method: string
  path: string
  headers: Record<string, string>
  body: unknown
  signal?: AbortSignal | null
}

type Handler = (call: MockCall) => { status?: number; body?: unknown } | undefined

/** Nahradí fetch; predvolene /calculate vráti výsledok pre predvolené hodnoty a /scenarios prázdny zoznam. */
export function mockApi(handler: Handler = () => undefined) {
  const calls: MockCall[] = []
  const fetchMock = vi.fn(async (url: string, init: RequestInit = {}) => {
    const call: MockCall = {
      method: init.method ?? 'GET',
      path: url.replace(/^.*\/api\/v1/, ''),
      headers: (init.headers ?? {}) as Record<string, string>,
      body: init.body ? JSON.parse(String(init.body)) : undefined,
      signal: init.signal,
    }
    calls.push(call)
    const custom = handler(call)
    const fallback =
      call.path === '/calculate'
        ? { body: calcDefault }
        : call.path === '/scenarios' && call.method === 'GET'
          ? { body: [] }
          : { status: 404, body: { errors: [{ field: null, code: 'not_found', message: 'x' }] } }
    const { status = 200, body } = custom ?? fallback
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return { calls, fetchMock, calculateCalls: () => calls.filter((c) => c.path === '/calculate') }
}
