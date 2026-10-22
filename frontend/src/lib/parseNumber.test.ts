import { describe, expect, it } from 'vitest'
import { parseNumber } from './parseNumber'

describe('parseNumber', () => {
  it('F01 prijme anglický aj slovenský formát', () => {
    expect(parseNumber('250,000.50')).toBe(250000.5)
    expect(parseNumber('250 000,50')).toBe(250000.5)
  })

  it.each([
    ['250000', 250000],
    ['250.000,50', 250000.5],
    ['250 000', 250000],
    ['250 000,5', 250000.5],
    ["1'250'000.75", 1250000.75],
    ['1,000,000', 1000000],
    ['250,000', 250000],
    ['4,5', 4.5],
    ['4.5', 4.5],
    ['  12  ', 12],
    ['-10', -10],
  ])('%s → %d', (raw, expected) => {
    expect(parseNumber(raw)).toBe(expected)
  })

  it.each(['', 'abc', '1,2,3.4.5', '12a', '--1'])('neplatné "%s" → null', (raw) => {
    expect(parseNumber(raw)).toBeNull()
  })

  it('decimalOnly berie jediný oddeľovač ako desatinný', () => {
    expect(parseNumber('4,125', { decimalOnly: true })).toBe(4.125)
    expect(parseNumber('4,125')).toBe(4125)
  })
})
