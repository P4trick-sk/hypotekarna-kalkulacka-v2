import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from '../App'
import calcExtra from '../test/fixtures/calc-extra200.json'
import { mockApi } from '../test/mockApi'

function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

const priceInput = () => screen.getByLabelText('Cena nehnuteľnosti', { selector: 'input[type=text]' })

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('CalculatorPage', () => {
  it('F02 po načítaní zobrazí výsledok pre predvolené hodnoty', async () => {
    const api = mockApi()
    renderApp()
    expect(await screen.findByTestId('monthly-total')).toHaveTextContent(/1,366\.04/)
    const [call] = api.calculateCalls()
    expect(call.body).toMatchObject({ price: '300000', down_payment: '60000', term_years: 30 })
    expect(call.headers['X-Log']).toBe('1')
  })

  it('F03 rýchle písanie pošle po debounce len jednu požiadavku', async () => {
    const api = mockApi()
    const user = userEvent.setup({ delay: null })
    renderApp()
    await screen.findByTestId('monthly-total')
    expect(api.calculateCalls()).toHaveLength(1)

    await user.clear(priceInput())
    await user.type(priceInput(), '350000')
    await waitFor(() => expect(api.calculateCalls()).toHaveLength(2))
    await new Promise((r) => setTimeout(r, 400))
    expect(api.calculateCalls()).toHaveLength(2)
    expect(api.calculateCalls()[1].body).toMatchObject({ price: '350000' })
    // druhý výpočet do 5 s sa už neloguje (F13)
    expect(api.calculateCalls()[1].headers['X-Log']).toBe('0')
  })

  it('F04 neplatný vstup zobrazí chybu, stlmí výsledky a nepošle požiadavku', async () => {
    const api = mockApi()
    const user = userEvent.setup()
    renderApp()
    await screen.findByTestId('monthly-total')

    const down = screen.getByLabelText('Akontácia', { selector: 'input' })
    await user.clear(down)
    await user.type(down, '400000')
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Akontácia musí byť nižšia ako cena nehnuteľnosti.',
    )
    expect(screen.getByTestId('results')).toHaveAttribute('data-stale', 'true')
    expect(down).toHaveAttribute('aria-invalid', 'true')
    await new Promise((r) => setTimeout(r, 400))
    expect(api.calculateCalls()).toHaveLength(1)
  })

  it('F05 nedostupné API zobrazí hlášku', async () => {
    mockApi((call) =>
      call.path === '/calculate' ? { status: 503, body: { errors: [] } } : undefined,
    )
    renderApp()
    expect(await screen.findByText(/Výpočet je dočasne nedostupný/)).toBeInTheDocument()
  })

  it('F06 akontácia v % sa prepočíta na sumu a naopak', async () => {
    mockApi()
    const user = userEvent.setup()
    renderApp()
    const percent = screen.getByLabelText('Akontácia v %', { selector: 'input[type=text]' })
    const amount = screen.getByLabelText('Akontácia', { selector: 'input' })
    expect(percent).toHaveValue('20')

    await user.clear(percent)
    await user.type(percent, '25')
    expect(amount).toHaveValue('75,000')

    await user.clear(amount)
    await user.type(amount, '30000')
    expect(percent).toHaveValue('10')
  })

  it('F07 aplikácia funguje, aj keď localStorage hádže výnimky', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    mockApi()
    renderApp()
    expect(await screen.findByTestId('monthly-total')).toHaveTextContent(/1,366\.04/)
  })

  it('obnoví posledné vstupy z localStorage (F9)', async () => {
    localStorage.setItem(
      'hk.inputs',
      JSON.stringify({ price: '500,000', downPayment: '100,000', currency: 'CZK' }),
    )
    const api = mockApi()
    renderApp()
    await waitFor(() => expect(api.calculateCalls()).toHaveLength(1))
    expect(api.calculateCalls()[0].body).toMatchObject({
      price: '500000',
      down_payment: '100000',
      currency: 'CZK',
    })
  })

  it('zobrazí odznak „skôr“ pri mimoriadnej splátke', async () => {
    mockApi((call) => (call.path === '/calculate' ? { body: calcExtra } : undefined))
    renderApp()
    expect(await screen.findByTestId('sooner')).toHaveTextContent('o 7 rokov a 6 mesiacov skôr')
  })

  it('F09 predvoľby doby a prepínač harmonogramu sú skupiny prepínačov', async () => {
    mockApi()
    renderApp()
    await screen.findByTestId('monthly-total')
    const term = screen.getByRole('radiogroup', { name: /Doba splatnosti/ })
    expect(within(term).getAllByRole('radio')).toHaveLength(5)
    expect(within(term).getByRole('radio', { name: '30 r.' })).toBeChecked()
    const view = screen.getByRole('radiogroup', { name: 'Zobrazenie harmonogramu' })
    await userEvent.click(within(view).getByRole('radio', { name: 'Mesačne' }))
    expect(screen.getAllByRole('row')).toHaveLength(361)
  })

  it('uloží scenár a zobrazí ho v zozname (F11)', async () => {
    const saved: unknown[] = []
    mockApi((call) => {
      if (call.path === '/scenarios' && call.method === 'POST') {
        const s = {
          id: 'a',
          name: (call.body as { name: string }).name,
          inputs: (call.body as { inputs: unknown }).inputs,
          currency: 'EUR',
          share_slug: null,
          share_url: null,
          monthly_total: '1366.04',
          created_at: '2026-10-22T08:00:00Z',
          updated_at: '2026-10-22T08:00:00Z',
        }
        saved.push(s)
        return { status: 201, body: s }
      }
      if (call.path === '/scenarios') {
        expect(call.headers['X-Client-Id']).toMatch(/^[0-9a-f-]{36}$/)
        return { body: saved }
      }
      return undefined
    })
    const user = userEvent.setup()
    renderApp()
    await screen.findByTestId('monthly-total')
    await user.type(screen.getByPlaceholderText(/Názov/), 'Byt Košice')
    await user.click(screen.getByRole('button', { name: 'Uložiť scenár' }))
    expect(await screen.findByText('Byt Košice')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Scenár je uložený.')
  })
})
