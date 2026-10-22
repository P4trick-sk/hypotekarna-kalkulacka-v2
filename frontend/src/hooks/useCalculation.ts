import { useEffect, useRef, useState } from 'react'
import { ApiRequestError, api } from '../api/client'
import type { ApiErrorItem, CalculationResult, LoanInputs } from '../api/types'

export const DEBOUNCE_MS = 250
/** F13: pri živom písaní logujeme najviac jeden výpočet za 5 s. */
export const LOG_INTERVAL_MS = 5000

export type CalcStatus = 'loading' | 'ok' | 'invalid' | 'unavailable'

export interface CalculationState {
  result: CalculationResult | null
  status: CalcStatus
  apiErrors: ApiErrorItem[]
}

/**
 * Prepočíta výsledok cez API pri každej zmene platných vstupov.
 * `inputs === null` znamená neplatný formulár: výsledok sa nemení, len sa označí ako neaktuálny.
 */
export function useCalculation(
  inputs: LoanInputs | null,
  source: 'live' | 'scenario' = 'live',
): CalculationState {
  const [state, setState] = useState<CalculationState>({
    result: null,
    status: 'loading',
    apiErrors: [],
  })
  const lastLogged = useRef(0)
  const key = inputs ? JSON.stringify(inputs) : null

  useEffect(() => {
    if (key === null) {
      setState((s) => ({ ...s, status: 'invalid', apiErrors: [] }))
      return
    }
    const controller = new AbortController()
    setState((s) => ({ ...s, status: 'loading' }))
    const timer = setTimeout(async () => {
      const now = Date.now()
      const log = now - lastLogged.current >= LOG_INTERVAL_MS
      try {
        const result = await api.calculate(JSON.parse(key) as LoanInputs, {
          signal: controller.signal,
          log,
          source,
        })
        if (log) lastLogged.current = now
        setState({ result, status: 'ok', apiErrors: [] })
      } catch (error) {
        if (controller.signal.aborted) return
        if (error instanceof ApiRequestError && !error.unavailable) {
          setState((s) => ({ ...s, status: 'invalid', apiErrors: error.errors }))
        } else {
          setState((s) => ({ ...s, status: 'unavailable', apiErrors: [] }))
        }
      }
    }, DEBOUNCE_MS)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [key, source])

  return state
}
