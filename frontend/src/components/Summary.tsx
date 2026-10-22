import type { CalculationResult } from '../api/types'
import { formatDuration, formatMoney, formatPercent, formatYearMonth } from '../lib/format'

interface Props {
  result: CalculationResult
  currency: string
}

export function Summary({ result, currency }: Props) {
  const s = result.summary
  const b = result.baseline
  const money = (v: string) => formatMoney(v, currency)
  const hasExtra = Number(s.monthly_extra) > 0

  const segments = [
    { key: 'principal', label: 'Istina', value: Number(s.first_principal) },
    { key: 'interest', label: 'Úrok', value: Number(s.first_interest) },
    { key: 'extra', label: 'Mimoriadna splátka', value: Number(s.monthly_extra) },
    { key: 'escrow', label: 'Daň a poistenie', value: Number(s.monthly_escrow) },
  ].filter((seg) => seg.value > 0)
  const total = segments.reduce((sum, seg) => sum + seg.value, 0) || 1

  return (
    <section className="summary" aria-label="Súhrn výsledkov">
      <div className="hero">
        <p className="eyebrow">Mesačná splátka</p>
        <p className="hero-value" data-testid="monthly-total">
          {money(s.monthly_total)}
        </p>
        <p className="hero-split">
          Istina a úrok {money(s.monthly_pi)}
          {hasExtra && <> · mimoriadna {money(s.monthly_extra)}</>}
          {Number(s.monthly_escrow) > 0 && <> · daň a poistenie {money(s.monthly_escrow)}</>}
        </p>
        {b && b.months_sooner > 0 && (
          <p className="badge" data-testid="sooner">
            Splatené {b.sooner_text}
          </p>
        )}

        <div
          className="breakdown"
          role="img"
          aria-label={`Rozdelenie prvej splátky: ${segments
            .map((seg) => `${seg.label} ${money(String(seg.value))}`)
            .join(', ')}`}
        >
          {segments.map((seg) => (
            <span
              key={seg.key}
              className={`seg seg-${seg.key}`}
              style={{ flexGrow: seg.value / total }}
            />
          ))}
        </div>
        <ul className="legend">
          {segments.map((seg) => (
            <li key={seg.key}>
              <span className={`dot seg-${seg.key}`} aria-hidden="true" />
              {seg.label} <strong>{money(String(seg.value))}</strong>
            </li>
          ))}
        </ul>
      </div>

      <dl className="stats">
        <div className="stat">
          <dt>Výška úveru</dt>
          <dd>{money(s.loan_amount)}</dd>
          <dd className="sub">
            Akontácia {formatPercent(s.down_payment_pct)} · LTV {formatPercent(s.ltv_pct)}
          </dd>
        </div>
        <div className="stat">
          <dt>Celkové úroky</dt>
          <dd>{money(s.total_interest)}</dd>
          <dd className="sub">
            {b && Number(b.interest_saved) > 0
              ? `Ušetríte ${money(b.interest_saved)}`
              : `${formatPercent(s.interest_pct_of_loan)} z úveru`}
          </dd>
        </div>
        <div className="stat">
          <dt>Celková cena úveru</dt>
          <dd>{money(s.total_cost)}</dd>
          <dd className="sub">istina + úroky</dd>
        </div>
        <div className="stat">
          <dt>Splatené</dt>
          <dd>{formatYearMonth(s.payoff_date)}</dd>
          <dd className="sub">
            {formatDuration(s.payments_count)} · {s.payments_count} splátok
          </dd>
        </div>
      </dl>
    </section>
  )
}
