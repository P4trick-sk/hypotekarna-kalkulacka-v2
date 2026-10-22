import { useId, useState } from 'react'
import { api } from '../api/client'
import type { CalculationResult, LoanInputs } from '../api/types'
import { formatMoney, formatYearMonth } from '../lib/format'

interface Props {
  result: CalculationResult
  inputs: LoanInputs | null
}

type View = 'yearly' | 'monthly'

export function ScheduleTable({ result, inputs }: Props) {
  const [view, setView] = useState<View>('yearly')
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const name = useId()
  const currency = inputs?.currency ?? 'EUR'
  const money = (v: string) => formatMoney(v, currency)

  const download = async () => {
    if (!inputs) return
    setDownloadError(null)
    try {
      const { blob, filename } = await api.exportCsv(inputs)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setDownloadError('CSV sa nepodarilo stiahnuť.')
    }
  }

  const rows =
    view === 'yearly'
      ? result.yearly.map((y) => ({ key: String(y.year), label: String(y.year), ...y }))
      : result.monthly.map((m) => ({
          key: String(m.n),
          label: `${m.n}. · ${formatYearMonth(m.date, 'short')}`,
          ...m,
        }))

  return (
    <section className="schedule" aria-label="Amortizačný harmonogram">
      <div className="schedule-head">
        <h2>Amortizačný harmonogram</h2>
        <div className="segmented" role="radiogroup" aria-label="Zobrazenie harmonogramu">
          {(['yearly', 'monthly'] as const).map((v) => (
            <label key={v} className="segment">
              <input
                type="radio"
                name={name}
                checked={view === v}
                onChange={() => setView(v)}
              />
              <span>{v === 'yearly' ? 'Ročne' : 'Mesačne'}</span>
            </label>
          ))}
        </div>
        <button type="button" className="btn" onClick={download} disabled={!inputs}>
          Stiahnuť CSV
        </button>
      </div>
      {downloadError && <p className="inline-error">{downloadError}</p>}
      <div className="table-wrap" tabIndex={0} aria-label="Tabuľka harmonogramu, posúvateľná">
        <table>
          <thead>
            <tr>
              <th scope="col">{view === 'yearly' ? 'Rok' : 'Splátka'}</th>
              <th scope="col">Zaplatené</th>
              <th scope="col">Istina</th>
              <th scope="col">Úrok</th>
              <th scope="col">Zostatok</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key}>
                <th scope="row">{r.label}</th>
                <td>{money(r.payment)}</td>
                <td>{money(r.principal)}</td>
                <td>{money(r.interest)}</td>
                <td>{money(r.balance)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
