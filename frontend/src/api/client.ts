import { getClientId } from '../lib/clientId'
import type {
  ApiErrorItem,
  CalculationResult,
  LoanInputs,
  Scenario,
  SharedScenario,
} from './types'

const BASE = `${(import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')}/api/v1`

export class ApiRequestError extends Error {
  readonly status: number
  readonly errors: ApiErrorItem[]

  constructor(status: number, errors: ApiErrorItem[]) {
    super(errors[0]?.message ?? `HTTP ${status}`)
    this.status = status
    this.errors = errors
  }

  /** Sieťová chyba, 5xx alebo 429 – kalkulačka je dočasne nedostupná (AK 11). */
  get unavailable(): boolean {
    return this.status === 0 || this.status >= 500 || this.status === 429
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
  signal?: AbortSignal
  withClient?: boolean
}

async function request(path: string, options: RequestOptions = {}): Promise<Response> {
  const headers: Record<string, string> = { ...options.headers }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (options.withClient) headers['X-Client-Id'] = getClientId()

  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiRequestError(0, [{ field: null, code: 'network', message: 'Sieťová chyba.' }])
  }

  if (!response.ok) {
    let errors: ApiErrorItem[] = []
    try {
      errors = ((await response.json()) as { errors?: ApiErrorItem[] }).errors ?? []
    } catch {
      // telo nie je JSON (napr. proxy chyba)
    }
    throw new ApiRequestError(response.status, errors)
  }
  return response
}

async function json<T>(path: string, options?: RequestOptions): Promise<T> {
  return (await request(path, options)).json() as Promise<T>
}

export interface CalculateOptions {
  signal?: AbortSignal
  log?: boolean
  source?: 'live' | 'scenario'
}

export const api = {
  calculate(inputs: LoanInputs, { signal, log = false, source = 'live' }: CalculateOptions = {}) {
    return json<CalculationResult>('/calculate', {
      method: 'POST',
      body: inputs,
      signal,
      headers: { 'X-Log': log ? '1' : '0', 'X-Log-Source': source },
    })
  },

  async exportCsv(inputs: LoanInputs): Promise<{ blob: Blob; filename: string }> {
    const response = await request('/export/csv', { method: 'POST', body: inputs })
    const disposition = response.headers.get('Content-Disposition') ?? ''
    const filename =
      /filename="([^"]+)"/.exec(disposition)?.[1] ??
      `mortgage-schedule-${inputs.currency.toLowerCase()}.csv`
    return { blob: await response.blob(), filename }
  },

  listScenarios() {
    return json<Scenario[]>('/scenarios', { withClient: true })
  },

  createScenario(name: string, inputs: LoanInputs) {
    return json<Scenario>('/scenarios', {
      method: 'POST',
      body: { name, inputs },
      withClient: true,
    })
  },

  updateScenario(id: string, changes: { name?: string; inputs?: LoanInputs }) {
    return json<Scenario>(`/scenarios/${id}`, { method: 'PATCH', body: changes, withClient: true })
  },

  async deleteScenario(id: string) {
    await request(`/scenarios/${id}`, { method: 'DELETE', withClient: true })
  },

  shareScenario(id: string) {
    return json<{ slug: string; url: string }>(`/scenarios/${id}/share`, {
      method: 'POST',
      withClient: true,
    })
  },

  async unshareScenario(id: string) {
    await request(`/scenarios/${id}/share`, { method: 'DELETE', withClient: true })
  },

  getShared(slug: string) {
    return json<SharedScenario>(`/share/${encodeURIComponent(slug)}`)
  },
}
