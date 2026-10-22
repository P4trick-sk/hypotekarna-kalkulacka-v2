import { describe, expect, it } from 'vitest'
import { defaultForm, type FormState } from './form'
import { validateForm } from './validate'

const codes = (patch: Partial<FormState>) => {
  const result = validateForm({ ...defaultForm(), ...patch })
  return result.ok ? [] : result.errors.map((e) => `${e.field}.${e.code}`)
}

describe('validateForm (zrkadlí api/calc/validation.py)', () => {
  it('predvolené hodnoty sú platné a prevedú sa na vstup API', () => {
    const result = validateForm({ ...defaultForm(), firstPayment: '2026-11' })
    expect(result).toEqual({
      ok: true,
      inputs: {
        price: '300000',
        down_payment: '60000',
        annual_rate: '4.5',
        term_years: 30,
        first_payment: '2026-11',
        extra_monthly: '0',
        tax_yearly: '1200',
        insurance_yearly: '600',
        currency: 'EUR',
      },
    })
  })

  it('V01 cena 0', () => expect(codes({ price: '0' })).toContain('price.gt_zero'))
  it('V02 akontácia = cena', () =>
    expect(codes({ downPayment: '300000' })).toEqual(['down_payment.gte_price']))
  it('V03 záporná akontácia', () =>
    expect(codes({ downPayment: '-1' })).toEqual(['down_payment.negative']))
  it('V04 sadzba nad 50 %', () =>
    expect(codes({ rate: '50,01' })).toEqual(['annual_rate.out_of_range']))
  it.each([
    ['0', 'out_of_range'],
    ['51', 'out_of_range'],
    ['12,5', 'not_integer'],
  ])('V05 doba %s', (termYears, code) =>
    expect(codes({ termYears })).toEqual([`term_years.${code}`]),
  )
  it('V06 záporná mimoriadna splátka', () =>
    expect(codes({ extra: '-10' })).toEqual(['extra_monthly.negative']))
  it('V08 viac chýb v poradí polí', () =>
    expect(codes({ rate: '60', price: '0' })).toEqual(['price.gt_zero', 'annual_rate.out_of_range']))
  it('V09 neplatný mesiac', () =>
    expect(codes({ firstPayment: '2026-13' })).toEqual(['first_payment.invalid_date']))
  it('prázdne voliteľné polia sú 0', () =>
    expect(codes({ extra: '', tax: '', insurance: '' })).toEqual([]))
  it('nečíselný vstup', () => expect(codes({ price: 'abc' })).toEqual(['price.invalid_number']))
})
