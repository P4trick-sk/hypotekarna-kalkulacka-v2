import type { CalculationResult, LoanInputs } from '../api/types'
import type { Theme } from '../hooks/useTheme'
import { BalanceChart, YearlyChart } from './Charts'
import { ScheduleTable } from './ScheduleTable'
import { Summary } from './Summary'

interface Props {
  result: CalculationResult | null
  inputs: LoanInputs | null
  currency: string
  theme: Theme
  stale: boolean
  busy: boolean
}

export function Results({ result, inputs, currency, theme, stale, busy }: Props) {
  if (!result) {
    return (
      <div className="results placeholder" aria-busy={busy}>
        <p>{busy ? 'Počítam…' : 'Výsledky sa zobrazia po zadaní platných údajov.'}</p>
      </div>
    )
  }
  return (
    <div
      className={`results${stale ? ' stale' : ''}`}
      aria-busy={busy}
      data-testid="results"
      data-stale={stale || undefined}
    >
      <Summary result={result} currency={currency} />
      <div className="charts">
        <BalanceChart key={`b-${theme}`} result={result} currency={currency} theme={theme} />
        <YearlyChart key={`y-${theme}`} result={result} currency={currency} theme={theme} />
      </div>
      <ScheduleTable result={result} inputs={stale ? null : inputs} />
    </div>
  )
}
