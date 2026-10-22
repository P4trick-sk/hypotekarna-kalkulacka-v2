// Formátovanie podľa jazyka prehliadača (F7). Mena mení len symbol, nekonvertuje.

const locale = () => (typeof navigator !== 'undefined' && navigator.language) || 'sk-SK'

export function formatMoney(value: string | number, currency: string, fractionDigits = 2): string {
  return new Intl.NumberFormat(locale(), {
    style: 'currency',
    currency,
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(Number(value))
}

export function formatNumber(value: number, maxFractionDigits = 2): string {
  return new Intl.NumberFormat(locale(), { maximumFractionDigits: maxFractionDigits }).format(value)
}

export function formatPercent(value: string | number): string {
  return `${formatNumber(Number(value))} %`
}

/** "2056-10" → "október 2056" */
export function formatYearMonth(ym: string, month: 'long' | 'short' = 'long'): string {
  const [year, m] = ym.split('-').map(Number)
  return new Intl.DateTimeFormat(locale(), { month, year: 'numeric' }).format(new Date(year, m - 1, 1))
}

export function formatDuration(months: number): string {
  const years = Math.floor(months / 12)
  const rest = months % 12
  const parts: string[] = []
  if (years) parts.push(`${years} ${plural(years, 'rok', 'roky', 'rokov')}`)
  if (rest) parts.push(`${rest} ${plural(rest, 'mesiac', 'mesiace', 'mesiacov')}`)
  return parts.join(' a ')
}

export function plural(count: number, one: string, few: string, many: string): string {
  if (count === 1) return one
  if (count >= 2 && count <= 4) return few
  return many
}

export function nextMonth(today = new Date()): string {
  const d = new Date(today.getFullYear(), today.getMonth() + 1, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}
