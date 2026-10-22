import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { CalculationResult } from '../api/types'
import type { Theme } from '../hooks/useTheme'
import { formatMoney } from '../lib/format'

interface Props {
  result: CalculationResult
  currency: string
  theme: Theme
}

/** SVG atribúty nepodporujú var(), preto farby čítame z CSS premenných pri každej zmene témy. */
function useChartColors(theme: Theme) {
  return useMemo(() => {
    const css = getComputedStyle(document.documentElement)
    const v = (name: string, fallback: string) => css.getPropertyValue(name).trim() || fallback
    return {
      principal: v('--c-principal', '#2f6fdb'),
      interest: v('--c-interest', '#e0803a'),
      baseline: v('--c-muted', '#8a94a6'),
      grid: v('--c-border', '#dde3ec'),
      text: v('--c-text-muted', '#5b6577'),
      surface: v('--c-surface', '#ffffff'),
    }
    // theme je zámerne závislosť – po prepnutí sa CSS premenné zmenia
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme])
}

const compact = (currency: string) => (value: number) =>
  new Intl.NumberFormat(navigator.language || 'sk-SK', {
    style: 'currency',
    currency,
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)

export function BalanceChart({ result, currency, theme }: Props) {
  const colors = useChartColors(theme)
  const data = useMemo(() => {
    const first = result.monthly[0]
    const [startYear, startMonth] = first.date.split('-').map(Number)
    const baselineByYear = new Map<number, number>()
    result.baseline?.balance.forEach((balance, i) => {
      const year = startYear + Math.floor((startMonth - 1 + i) / 12)
      baselineByYear.set(year, Number(balance))
    })
    const years = new Set([...result.yearly.map((y) => y.year), ...baselineByYear.keys()])
    const actual = new Map(result.yearly.map((y) => [y.year, Number(y.balance)]))
    return [...years]
      .sort((a, b) => a - b)
      .map((year) => ({
        year,
        balance: actual.get(year) ?? (year > result.yearly.at(-1)!.year ? 0 : undefined),
        baseline: result.baseline ? (baselineByYear.get(year) ?? 0) : undefined,
      }))
  }, [result])

  return (
    <figure className="chart-card">
      <figcaption>Zostatok úveru na konci roka</figcaption>
      <div className="chart" tabIndex={-1}>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }} accessibilityLayer>
            <CartesianGrid stroke={colors.grid} vertical={false} />
            <XAxis dataKey="year" stroke={colors.text} tickLine={false} minTickGap={16} />
            <YAxis
              stroke={colors.text}
              tickFormatter={compact(currency)}
              width={72}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              formatter={(value) => formatMoney(Number(value), currency, 0)}
              contentStyle={{ background: colors.surface, borderColor: colors.grid }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="balance"
              name={result.baseline ? 'S mimoriadnou splátkou' : 'Zostatok'}
              stroke={colors.principal}
              strokeWidth={2.5}
              dot={false}
              connectNulls
            />
            {result.baseline && (
              <Line
                type="monotone"
                dataKey="baseline"
                name="Bez mimoriadnej splátky"
                stroke={colors.baseline}
                strokeWidth={2}
                strokeDasharray="5 4"
                dot={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}

export function YearlyChart({ result, currency, theme }: Props) {
  const colors = useChartColors(theme)
  const data = useMemo(
    () =>
      result.yearly.map((y) => ({
        year: y.year,
        principal: Number(y.principal),
        interest: Number(y.interest),
      })),
    [result],
  )
  return (
    <figure className="chart-card">
      <figcaption>Istina a úrok podľa rokov</figcaption>
      <div className="chart">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }} accessibilityLayer>
            <CartesianGrid stroke={colors.grid} vertical={false} />
            <XAxis dataKey="year" stroke={colors.text} tickLine={false} minTickGap={16} />
            <YAxis
              stroke={colors.text}
              tickFormatter={compact(currency)}
              width={72}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              formatter={(value) => formatMoney(Number(value), currency)}
              contentStyle={{ background: colors.surface, borderColor: colors.grid }}
            />
            <Legend />
            <Bar dataKey="principal" name="Istina" stackId="a" fill={colors.principal} />
            <Bar dataKey="interest" name="Úrok" stackId="a" fill={colors.interest} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}
