import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from '../App'
import calcDefault from '../test/fixtures/calc-default.json'
import { mockApi } from '../test/mockApi'

const shared = {
  name: 'Byt Košice',
  currency: 'EUR',
  inputs: {
    price: '300000.00',
    down_payment: '60000.00',
    annual_rate: '4.5',
    term_years: 30,
    first_payment: '2026-11',
    extra_monthly: '0.00',
    tax_yearly: '1200.00',
    insurance_yearly: '600.00',
    currency: 'EUR',
  },
  result: calcDefault,
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('SharePage', () => {
  it('F08 zobrazí zdieľaný scenár len na čítanie', async () => {
    mockApi((call) => (call.path === '/share/AbCdEf1234' ? { body: shared } : undefined))
    renderAt('/s/AbCdEf1234')
    expect(await screen.findByRole('heading', { name: 'Byt Košice' })).toBeInTheDocument()
    expect(screen.getByTestId('monthly-total')).toHaveTextContent(/1,366\.04/)
    expect(screen.getByLabelText('Cena nehnuteľnosti', { selector: 'input[type=text]' })).toHaveAttribute(
      'readonly',
    )
    expect(screen.queryByRole('button', { name: 'Obnoviť predvolené' })).not.toBeInTheDocument()
  })

  it('Otvoriť v kalkulačke skopíruje vstupy do vlastnej kalkulačky', async () => {
    const api = mockApi((call) =>
      call.path === '/share/AbCdEf1234' ? { body: shared } : undefined,
    )
    renderAt('/s/AbCdEf1234')
    await userEvent.click(await screen.findByRole('button', { name: 'Otvoriť v kalkulačke' }))
    expect(await screen.findByRole('heading', { name: 'Parametre úveru' })).toBeInTheDocument()
    expect(JSON.parse(localStorage.getItem('hk.inputs')!)).toMatchObject({ firstPayment: '2026-11' })
    await screen.findByTestId('monthly-total')
    expect(api.calculateCalls()[0].body).toMatchObject({ first_payment: '2026-11' })
  })

  it('zrušený odkaz zobrazí „Odkaz už neplatí“', async () => {
    mockApi()
    renderAt('/s/Neexistuje')
    expect(await screen.findByRole('heading', { name: 'Odkaz už neplatí' })).toBeInTheDocument()
  })
})
