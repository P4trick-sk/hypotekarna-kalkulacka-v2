import type { Currency, LoanInputs } from '../api/types'
import { formatNumber, nextMonth } from './format'
import { parseNumber } from './parseNumber'

/** Stav formulára – texty tak, ako ich používateľ napísal. */
export interface FormState {
  price: string
  downPayment: string
  rate: string
  termYears: string
  firstPayment: string
  extra: string
  tax: string
  insurance: string
  currency: Currency
}

export function defaultForm(): FormState {
  return {
    price: formatNumber(300000),
    downPayment: formatNumber(60000),
    rate: formatNumber(4.5),
    termYears: '30',
    firstPayment: nextMonth(),
    extra: '0',
    tax: formatNumber(1200),
    insurance: formatNumber(600),
    currency: 'EUR',
  }
}

export function fromLoanInputs(inputs: LoanInputs): FormState {
  return {
    price: formatNumber(Number(inputs.price)),
    downPayment: formatNumber(Number(inputs.down_payment)),
    rate: formatNumber(Number(inputs.annual_rate), 3),
    termYears: String(inputs.term_years),
    firstPayment: inputs.first_payment,
    extra: formatNumber(Number(inputs.extra_monthly)),
    tax: formatNumber(Number(inputs.tax_yearly)),
    insurance: formatNumber(Number(inputs.insurance_yearly)),
    currency: inputs.currency,
  }
}

/** Percento akontácie z textov formulára (F1: suma a % sú synchronizované). */
export function downPaymentPercent(form: FormState): number | null {
  const price = parseNumber(form.price)
  const down = parseNumber(form.downPayment)
  if (price === null || down === null || price <= 0) return null
  return (down / price) * 100
}

export function downPaymentFromPercent(form: FormState, percent: number): string {
  const price = parseNumber(form.price) ?? 0
  return formatNumber(Math.round((price * percent) / 100))
}
