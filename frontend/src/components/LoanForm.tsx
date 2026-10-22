import { useId, useState } from 'react'
import { CURRENCIES } from '../api/types'
import { downPaymentFromPercent, downPaymentPercent, type FormState } from '../lib/form'
import { formatNumber } from '../lib/format'
import { parseNumber } from '../lib/parseNumber'

const TERM_PRESETS = [10, 15, 20, 25, 30]

interface Props {
  form: FormState
  onChange: (patch: Partial<FormState>) => void
  onReset?: () => void
  invalidField?: string | null
  readOnly?: boolean
}

interface NumberFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  suffix?: string
  slider?: { min: number; max: number; step: number }
  decimalOnly?: boolean
  invalid?: boolean
  readOnly?: boolean
  hint?: string
}

function NumberField({
  label,
  value,
  onChange,
  suffix,
  slider,
  decimalOnly,
  invalid,
  readOnly,
  hint,
}: NumberFieldProps) {
  const id = useId()
  // Počas písania drží pole vlastný text; inak by odvodené pole (akontácia v %) prepisovalo rozpísanú hodnotu.
  const [draft, setDraft] = useState<string | null>(null)
  const parsed = parseNumber(value, { decimalOnly })
  const reformat = () => {
    setDraft(null)
    if (parsed !== null) onChange(formatNumber(parsed, decimalOnly ? 3 : 2))
  }
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="input-affix">
        <input
          id={id}
          type="text"
          inputMode="decimal"
          autoComplete="off"
          value={draft ?? value}
          aria-invalid={invalid || undefined}
          aria-describedby={hint ? `${id}-hint` : undefined}
          readOnly={readOnly}
          onFocus={() => !readOnly && setDraft(value)}
          onChange={(e) => {
            setDraft(e.target.value)
            onChange(e.target.value)
          }}
          onBlur={reformat}
        />
        {suffix && <span className="affix">{suffix}</span>}
      </div>
      {hint && (
        <small id={`${id}-hint`} className="hint">
          {hint}
        </small>
      )}
      {slider && !readOnly && (
        <input
          type="range"
          aria-label={`${label} – posuvník`}
          min={slider.min}
          max={slider.max}
          step={slider.step}
          value={Math.min(Math.max(parsed ?? slider.min, slider.min), slider.max)}
          onChange={(e) => onChange(formatNumber(Number(e.target.value), decimalOnly ? 3 : 2))}
        />
      )}
    </div>
  )
}

export function LoanForm({ form, onChange, onReset, invalidField, readOnly }: Props) {
  const termId = useId()
  const currencySymbol = form.currency
  const percent = downPaymentPercent(form)
  const isPreset = TERM_PRESETS.includes(Number(form.termYears))

  return (
    <form className="loan-form" onSubmit={(e) => e.preventDefault()} aria-label="Parametre úveru">
      <NumberField
        label="Cena nehnuteľnosti"
        value={form.price}
        onChange={(price) => onChange({ price })}
        suffix={currencySymbol}
        slider={{ min: 20000, max: 2000000, step: 5000 }}
        invalid={invalidField === 'price'}
        readOnly={readOnly}
      />

      <div className="field-pair">
        <NumberField
          label="Akontácia"
          value={form.downPayment}
          onChange={(downPayment) => onChange({ downPayment })}
          suffix={currencySymbol}
          invalid={invalidField === 'down_payment'}
          readOnly={readOnly}
        />
        <NumberField
          label="Akontácia v %"
          value={percent === null ? '' : formatNumber(percent, 1)}
          onChange={(raw) => {
            const pct = parseNumber(raw, { decimalOnly: true })
            if (pct !== null) onChange({ downPayment: downPaymentFromPercent(form, pct) })
          }}
          suffix="%"
          slider={{ min: 0, max: 100, step: 1 }}
          decimalOnly
          invalid={invalidField === 'down_payment'}
          readOnly={readOnly}
        />
      </div>

      <NumberField
        label="Úroková sadzba (ročne)"
        value={form.rate}
        onChange={(rate) => onChange({ rate })}
        suffix="%"
        slider={{ min: 0, max: 15, step: 0.05 }}
        decimalOnly
        invalid={invalidField === 'annual_rate'}
        readOnly={readOnly}
      />

      <fieldset className="field" aria-invalid={invalidField === 'term_years' || undefined}>
        <legend>Doba splatnosti</legend>
        <div className="segmented" role="radiogroup" aria-label="Doba splatnosti – predvoľby">
          {TERM_PRESETS.map((years) => (
            <label key={years} className="segment">
              <input
                type="radio"
                name={termId}
                value={years}
                checked={Number(form.termYears) === years}
                disabled={readOnly}
                onChange={() => onChange({ termYears: String(years) })}
              />
              <span>{years} r.</span>
            </label>
          ))}
        </div>
        <div className="input-affix custom-term">
          <input
            type="text"
            inputMode="numeric"
            aria-label="Vlastná doba splatnosti v rokoch"
            value={isPreset ? '' : form.termYears}
            placeholder={isPreset ? 'Vlastná' : ''}
            readOnly={readOnly}
            aria-invalid={invalidField === 'term_years' || undefined}
            onChange={(e) => onChange({ termYears: e.target.value })}
          />
          <span className="affix">rokov</span>
        </div>
      </fieldset>

      <div className="field">
        <label htmlFor={`${termId}-first`}>Prvá splátka</label>
        <input
          id={`${termId}-first`}
          type="month"
          value={form.firstPayment}
          readOnly={readOnly}
          aria-invalid={invalidField === 'first_payment' || undefined}
          onChange={(e) => onChange({ firstPayment: e.target.value })}
        />
      </div>

      <NumberField
        label="Mimoriadna mesačná splátka"
        value={form.extra}
        onChange={(extra) => onChange({ extra })}
        suffix={currencySymbol}
        slider={{ min: 0, max: 3000, step: 50 }}
        invalid={invalidField === 'extra_monthly'}
        readOnly={readOnly}
        hint="Voliteľné – navyše k riadnej splátke, celé ide na istinu."
      />

      <div className="field-pair">
        <NumberField
          label="Daň z nehnuteľnosti / rok"
          value={form.tax}
          onChange={(tax) => onChange({ tax })}
          suffix={currencySymbol}
          invalid={invalidField === 'tax_yearly'}
          readOnly={readOnly}
        />
        <NumberField
          label="Poistenie / rok"
          value={form.insurance}
          onChange={(insurance) => onChange({ insurance })}
          suffix={currencySymbol}
          invalid={invalidField === 'insurance_yearly'}
          readOnly={readOnly}
        />
      </div>

      <div className="form-footer">
        <div className="field currency">
          <label htmlFor={`${termId}-currency`}>Mena</label>
          <select
            id={`${termId}-currency`}
            value={form.currency}
            disabled={readOnly}
            onChange={(e) => onChange({ currency: e.target.value as FormState['currency'] })}
          >
            {CURRENCIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
        {onReset && !readOnly && (
          <button type="button" className="btn ghost" onClick={onReset}>
            Obnoviť predvolené
          </button>
        )}
      </div>
    </form>
  )
}
