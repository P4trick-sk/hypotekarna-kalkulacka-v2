import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiRequestError, api } from '../api/client'
import type { SharedScenario } from '../api/types'
import { LoanForm } from '../components/LoanForm'
import { Results } from '../components/Results'
import type { Theme } from '../hooks/useTheme'
import { fromLoanInputs } from '../lib/form'
import { KEYS, writeJson } from '../lib/storage'

type State =
  | { kind: 'loading' }
  | { kind: 'ok'; data: SharedScenario }
  | { kind: 'gone' }
  | { kind: 'error' }

export function SharePage({ theme }: { theme: Theme }) {
  const { slug = '' } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false
    api
      .getShared(slug)
      .then((data) => !cancelled && setState({ kind: 'ok', data }))
      .catch((error: unknown) => {
        if (cancelled) return
        const gone = error instanceof ApiRequestError && error.status === 404
        setState({ kind: gone ? 'gone' : 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [slug])

  if (state.kind === 'loading') {
    return (
      <main className="layout single" aria-busy="true">
        <p>Načítavam zdieľaný scenár…</p>
      </main>
    )
  }
  if (state.kind !== 'ok') {
    return (
      <main className="layout single">
        <section className="card notice">
          <h1>{state.kind === 'gone' ? 'Odkaz už neplatí' : 'Scenár sa nepodarilo načítať'}</h1>
          <p>
            {state.kind === 'gone'
              ? 'Vlastník zdieľanie zrušil alebo odkaz neexistuje.'
              : 'Služba je dočasne nedostupná. Skúste to o chvíľu znova.'}
          </p>
          <Link to="/" className="btn primary">
            Otvoriť kalkulačku
          </Link>
        </section>
      </main>
    )
  }

  const { data } = state
  const form = fromLoanInputs(data.inputs)
  const openInCalculator = () => {
    writeJson(KEYS.inputs, form)
    navigate('/')
  }

  return (
    <main className="layout">
      <div className="column-inputs">
        <section className="card" aria-labelledby="share-title">
          <p className="eyebrow">Zdieľaný scenár · len na čítanie</p>
          <h1 id="share-title">{data.name}</h1>
          <LoanForm form={form} onChange={() => {}} readOnly />
          <button type="button" className="btn primary wide" onClick={openInCalculator}>
            Otvoriť v kalkulačke
          </button>
        </section>
      </div>
      <div className="column-results">
        <Results
          result={data.result}
          inputs={data.inputs}
          currency={data.currency}
          theme={theme}
          stale={false}
          busy={false}
        />
      </div>
    </main>
  )
}
