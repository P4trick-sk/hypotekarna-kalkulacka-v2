// Kópia pravidiel z api/calc/validation.py (rovnaké kódy a hlášky, 04-review R12).
// Zdroj pravdy je API; táto validácia slúži len na okamžitú odozvu.

import { CURRENCIES, type LoanInputs } from '../api/types'
import type { FormState } from './form'
import { parseNumber } from './parseNumber'

export interface FieldError {
  field: keyof LoanInputs
  code: string
  message: string
}

const MESSAGES: Record<string, string> = {
  'price.gt_zero': 'Cena nehnuteľnosti musí byť väčšia ako 0.',
  'down_payment.negative': 'Akontácia nemôže byť záporná.',
  'down_payment.gte_price': 'Akontácia musí byť nižšia ako cena nehnuteľnosti.',
  'annual_rate.out_of_range': 'Úroková sadzba musí byť od 0 do 50 %.',
  'term_years.not_integer': 'Doba splatnosti musí byť v celých rokoch.',
  'term_years.out_of_range': 'Doba splatnosti musí byť od 1 do 50 rokov.',
  'first_payment.invalid_date': 'Prvá splátka musí byť platný mesiac a rok.',
  'extra_monthly.negative': 'Mimoriadna splátka nemôže byť záporná.',
  'tax_yearly.negative': 'Daň z nehnuteľnosti nemôže byť záporná.',
  'insurance_yearly.negative': 'Poistenie nemôže byť záporné.',
  'currency.unsupported': 'Táto mena nie je podporovaná.',
  invalid_number: 'Zadaj platné číslo.',
}

function err(field: keyof LoanInputs, code: string): FieldError {
  return { field, code, message: MESSAGES[`${field}.${code}`] ?? MESSAGES[code] }
}

export type ValidationResult =
  | { ok: true; inputs: LoanInputs }
  | { ok: false; errors: FieldError[] }

/** Prevedie formulár na vstup API alebo vráti chyby v poradí polí z F1. */
export function validateForm(form: FormState): ValidationResult {
  const errors: FieldError[] = []
  const num = (
    field: keyof LoanInputs,
    raw: string,
    fallbackZero = false,
    decimalOnly = false,
  ): number | null => {
    if (fallbackZero && raw.trim() === '') return 0
    const value = parseNumber(raw, { decimalOnly })
    if (value === null) errors.push(err(field, 'invalid_number'))
    return value
  }

  const price = num('price', form.price)
  if (price !== null && price <= 0) errors.push(err('price', 'gt_zero'))

  const down = num('down_payment', form.downPayment, true)
  if (down !== null) {
    if (down < 0) errors.push(err('down_payment', 'negative'))
    else if (price !== null && price > 0 && down >= price)
      errors.push(err('down_payment', 'gte_price'))
  }

  const rate = num('annual_rate', form.rate, false, true)
  if (rate !== null && (rate < 0 || rate > 50)) errors.push(err('annual_rate', 'out_of_range'))

  const term = num('term_years', form.termYears, false, true)
  if (term !== null) {
    if (!Number.isInteger(term)) errors.push(err('term_years', 'not_integer'))
    else if (term < 1 || term > 50) errors.push(err('term_years', 'out_of_range'))
  }

  const match = /^(\d{4})-(\d{2})$/.exec(form.firstPayment)
  if (!match || Number(match[2]) < 1 || Number(match[2]) > 12)
    errors.push(err('first_payment', 'invalid_date'))

  const extra = num('extra_monthly', form.extra, true)
  if (extra !== null && extra < 0) errors.push(err('extra_monthly', 'negative'))
  const tax = num('tax_yearly', form.tax, true)
  if (tax !== null && tax < 0) errors.push(err('tax_yearly', 'negative'))
  const insurance = num('insurance_yearly', form.insurance, true)
  if (insurance !== null && insurance < 0) errors.push(err('insurance_yearly', 'negative'))

  if (!CURRENCIES.includes(form.currency)) errors.push(err('currency', 'unsupported'))

  if (errors.length) return { ok: false, errors }
  return {
    ok: true,
    inputs: {
      price: String(price),
      down_payment: String(down),
      annual_rate: String(rate),
      term_years: term as number,
      first_payment: form.firstPayment,
      extra_monthly: String(extra),
      tax_yearly: String(tax),
      insurance_yearly: String(insurance),
      currency: form.currency,
    },
  }
}
