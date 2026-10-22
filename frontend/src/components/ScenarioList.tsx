import { useCallback, useEffect, useId, useState } from 'react'
import { ApiRequestError, api } from '../api/client'
import type { LoanInputs, Scenario } from '../api/types'
import { formatMoney } from '../lib/format'

interface Props {
  inputs: LoanInputs | null
  onLoad: (scenario: Scenario) => void
}

type Status = 'loading' | 'ready' | 'unavailable'

function describe(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.unavailable) return 'Ukladanie scenárov je teraz nedostupné.'
    return error.errors[0]?.message ?? 'Akcia zlyhala.'
  }
  return 'Akcia zlyhala.'
}

export function ScenarioList({ inputs, onLoad }: Props) {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [status, setStatus] = useState<Status>('loading')
  const [name, setName] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [renaming, setRenaming] = useState<{ id: string; name: string } | null>(null)
  const nameId = useId()

  const refresh = useCallback(async () => {
    try {
      setScenarios(await api.listScenarios())
      setStatus('ready')
    } catch {
      setStatus('unavailable')
    }
  }, [])

  useEffect(() => {
    // načítanie zoznamu pri prvom zobrazení
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh()
  }, [refresh])

  const run = async (action: () => Promise<unknown>, success?: string) => {
    setMessage(null)
    try {
      await action()
      await refresh()
      if (success) setMessage(success)
    } catch (error) {
      setMessage(describe(error))
    }
  }

  const save = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputs || !name.trim()) return
    void run(async () => {
      await api.createScenario(name.trim(), inputs)
      setName('')
    }, 'Scenár je uložený.')
  }

  const share = (s: Scenario) =>
    run(async () => {
      const { url } = await api.shareScenario(s.id)
      try {
        await navigator.clipboard.writeText(url)
      } catch {
        // schránka nemusí byť dostupná; odkaz je aj v zozname
      }
    }, 'Odkaz na zdieľanie je skopírovaný do schránky.')

  const rename = (e: React.FormEvent) => {
    e.preventDefault()
    if (!renaming || !renaming.name.trim()) return
    const { id, name: newName } = renaming
    void run(async () => {
      await api.updateScenario(id, { name: newName.trim() })
      setRenaming(null)
    })
  }

  return (
    <section className="scenarios" aria-labelledby={`${nameId}-title`}>
      <h2 id={`${nameId}-title`}>Moje scenáre</h2>
      <p className="hint">
        Scenáre sú uložené k tomuto prehliadaču. Po vymazaní dát prehliadača ich už neuvidíte.
      </p>

      {status === 'unavailable' ? (
        <p className="inline-error">
          Ukladanie scenárov je nedostupné – databáza nie je pripojená.
        </p>
      ) : (
        <>
          <form className="save-form" onSubmit={save}>
            <label htmlFor={nameId} className="visually-hidden">
              Názov scenára
            </label>
            <input
              id={nameId}
              type="text"
              placeholder="Názov, napr. Byt Košice"
              maxLength={100}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <button type="submit" className="btn primary" disabled={!inputs || !name.trim()}>
              Uložiť scenár
            </button>
          </form>

          <p className="status" role="status">
            {message}
          </p>

          {status === 'loading' && <p className="hint">Načítavam…</p>}
          {status === 'ready' && scenarios.length === 0 && (
            <p className="hint">Zatiaľ nemáte uložené žiadne scenáre.</p>
          )}

          <ul className="scenario-list">
            {scenarios.map((s) => (
              <li key={s.id} className="scenario">
                {renaming?.id === s.id ? (
                  <form className="rename-form" onSubmit={rename}>
                    <input
                      aria-label="Nový názov"
                      maxLength={100}
                      value={renaming.name}
                      autoFocus
                      onChange={(e) => setRenaming({ id: s.id, name: e.target.value })}
                    />
                    <button type="submit" className="btn small primary">
                      Uložiť
                    </button>
                    <button type="button" className="btn small ghost" onClick={() => setRenaming(null)}>
                      Zrušiť
                    </button>
                  </form>
                ) : (
                  <div className="scenario-head">
                    <strong>{s.name}</strong>
                    <span className="scenario-meta">
                      {s.monthly_total ? formatMoney(s.monthly_total, s.currency) : '—'} / mes. ·{' '}
                      {new Date(s.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {s.share_url && (
                  <p className="share-url">
                    Zdieľané: <a href={s.share_url}>{s.share_url}</a>
                  </p>
                )}
                <div className="scenario-actions">
                  <button type="button" className="btn small" onClick={() => onLoad(s)}>
                    Načítať
                  </button>
                  <button
                    type="button"
                    className="btn small"
                    disabled={!inputs}
                    onClick={() =>
                      inputs &&
                      run(() => api.updateScenario(s.id, { inputs }), 'Scenár je prepísaný.')
                    }
                  >
                    Prepísať
                  </button>
                  <button
                    type="button"
                    className="btn small"
                    onClick={() => setRenaming({ id: s.id, name: s.name })}
                  >
                    Premenovať
                  </button>
                  {s.share_slug ? (
                    <button
                      type="button"
                      className="btn small"
                      onClick={() =>
                        run(() => api.unshareScenario(s.id), 'Zdieľanie je zrušené.')
                      }
                    >
                      Zrušiť zdieľanie
                    </button>
                  ) : (
                    <button type="button" className="btn small" onClick={() => share(s)}>
                      Zdieľať
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn small danger"
                    onClick={() => {
                      if (window.confirm(`Naozaj zmazať scenár „${s.name}“?`))
                        void run(() => api.deleteScenario(s.id), 'Scenár je zmazaný.')
                    }}
                  >
                    Zmazať
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
