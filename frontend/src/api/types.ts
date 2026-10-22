// Typy zodpovedajú Pydantic schémam v api/app/schemas. Sumy sú reťazce ("1216.04").

export const CURRENCIES = ['EUR', 'USD', 'GBP', 'CZK', 'CHF', 'PLN'] as const
export type Currency = (typeof CURRENCIES)[number]

export interface LoanInputs {
  price: string
  down_payment: string
  annual_rate: string
  term_years: number
  first_payment: string
  extra_monthly: string
  tax_yearly: string
  insurance_yearly: string
  currency: Currency
}

export interface Summary {
  loan_amount: string
  down_payment_pct: string
  ltv_pct: string
  monthly_pi: string
  monthly_extra: string
  monthly_escrow: string
  monthly_total: string
  first_principal: string
  first_interest: string
  total_interest: string
  interest_pct_of_loan: string
  total_cost: string
  payoff_date: string
  payments_count: number
}

export interface PaymentRow {
  n: number
  date: string
  payment: string
  principal: string
  interest: string
  balance: string
}

export interface YearRow {
  year: number
  payment: string
  principal: string
  interest: string
  balance: string
}

export interface Baseline {
  payments_count: number
  total_interest: string
  interest_saved: string
  months_sooner: number
  sooner_text: string
  balance: string[]
}

export interface CalculationResult {
  summary: Summary
  monthly: PaymentRow[]
  yearly: YearRow[]
  baseline: Baseline | null
}

export interface ApiErrorItem {
  field: string | null
  code: string
  message: string
}

export interface Scenario {
  id: string
  name: string
  inputs: LoanInputs
  currency: Currency
  share_slug: string | null
  share_url: string | null
  monthly_total: string | null
  created_at: string
  updated_at: string
}

export interface SharedScenario {
  name: string
  inputs: LoanInputs
  currency: Currency
  result: CalculationResult
}
