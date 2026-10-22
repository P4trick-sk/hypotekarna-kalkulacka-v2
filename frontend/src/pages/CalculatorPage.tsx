import { useCallback, useMemo, useState } from 'react'
import type { Scenario } from '../api/types'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoanForm } from '../components/LoanForm'
import { Results } from '../components/Results'
import { ScenarioList } from '../components/ScenarioList'
import { useCalculation } from '../hooks/useCalculation'
import { usePersistentForm } from '../hooks/usePersistentForm'
import type { Theme } from '../hooks/useTheme'
import { defaultForm, fromLoanInputs, type FormState } from '../lib/form'
import { validateForm } from '../lib/validate'

const isValid = (form: FormState) => validateForm(form).ok

export function CalculatorPage({ theme }: { theme: Theme }) {
  const [form, setForm] = usePersistentForm(isValid)
  const [source, setSource] = useState<'live' | 'scenario'>('live')
  const validation = useMemo(() => validateForm(form), [form])
  const inputs = validation.ok ? validation.inputs : null
  const calc = useCalculation(inputs, source)

  const update = useCallback(
    (patch: Partial<FormState>) => {
      setSource('live')
      setForm((f) => ({ ...f, ...patch }))
    },
    [setForm],
  )

  const loadScenario = (scenario: Scenario) => {
    setSource('scenario')
    setForm(fromLoanInputs(scenario.inputs))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const firstError = !validation.ok ? validation.errors[0] : (calc.apiErrors[0] ?? null)
  const message =
    firstError?.message ??
    (calc.status === 'unavailable'
      ? 'Výpočet je dočasne nedostupný. Skúste to o chvíľu znova.'
      : null)

  return (
    <main className="layout">
      <div className="column-inputs">
        <section className="card" aria-labelledby="inputs-title">
          <h1 id="inputs-title">Parametre úveru</h1>
          <LoanForm
            form={form}
            onChange={update}
            onReset={() => update(defaultForm())}
            invalidField={firstError?.field ?? null}
          />
        </section>
        <section className="card">
          <ScenarioList inputs={inputs} onLoad={loadScenario} />
        </section>
      </div>
      <div className="column-results">
        <ErrorBanner message={message} />
        <Results
          result={calc.result}
          inputs={inputs}
          currency={calc.result && inputs ? inputs.currency : form.currency}
          theme={theme}
          stale={calc.status === 'invalid' || calc.status === 'unavailable'}
          busy={calc.status === 'loading'}
        />
        <p className="disclaimer">
          Výsledky sú orientačné. Ponuka banky sa môže líšiť kvôli poplatkom, zaokrúhľovaniu a
          zmenám sadzieb.
        </p>
      </div>
    </main>
  )
}
