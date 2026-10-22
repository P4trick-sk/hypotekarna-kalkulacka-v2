/**
 * Prečíta číslo zadané v ľubovoľnom bežnom formáte (F1):
 * "250,000.50", "250 000,50", "250.000,50", "250000", "4,5", "4.5".
 * Vráti null, ak to nie je číslo.
 *
 * `decimalOnly` (úroková sadzba, roky): jediný oddeľovač je vždy desatinný, takže "4,125" = 4.125.
 */
export function parseNumber(raw: string, { decimalOnly = false } = {}): number | null {
  // medzery vrátane nezlomiteľných (U+00A0, U+202F) a apostrofy (švajčiarsky formát)
  let s = raw.trim().replace(/[\s\u00a0\u202f'\u2019]/g, '')
  if (s === '') return null

  const lastComma = s.lastIndexOf(',')
  const lastDot = s.lastIndexOf('.')

  if (lastComma >= 0 && lastDot >= 0) {
    // Oddeľovač, ktorý je posledný, je desatinný.
    const decimal = lastComma > lastDot ? ',' : '.'
    const thousands = decimal === ',' ? '.' : ','
    s = s.split(thousands).join('').replace(decimal, '.')
  } else if (lastComma >= 0) {
    s = decimalOnly ? s.replace(',', '.') : resolveSingleSeparator(s, ',')
  } else if (lastDot >= 0 && !decimalOnly) {
    s = resolveSingleSeparator(s, '.')
  }

  if (!/^-?\d+(\.\d+)?$/.test(s)) return null
  return Number(s)
}

function resolveSingleSeparator(s: string, sep: string): string {
  const parts = s.split(sep)
  // "1,000,000" alebo "1.000.000" – viac výskytov sú tisíce
  if (parts.length > 2) return parts.join('')
  // "250,000" – čiarka a presne 3 číslice za ňou sú tisíce; "250.000" berieme ako desatinné číslo
  if (sep === ',' && parts[1].length === 3) return parts.join('')
  return parts.join('.')
}
