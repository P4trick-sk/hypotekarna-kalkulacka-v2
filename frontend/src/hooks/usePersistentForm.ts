import { useEffect, useState } from 'react'
import { CURRENCIES } from '../api/types'
import { defaultForm, type FormState } from '../lib/form'
import { KEYS, readJson, writeJson } from '../lib/storage'

function restore(): FormState {
  const saved = readJson<Partial<FormState>>(KEYS.inputs)
  const defaults = defaultForm()
  if (!saved || typeof saved !== 'object') return defaults
  const merged = { ...defaults }
  for (const key of Object.keys(defaults) as (keyof FormState)[]) {
    const value = saved[key]
    if (typeof value === 'string') (merged as Record<string, string>)[key] = value
  }
  if (!CURRENCIES.includes(merged.currency)) merged.currency = defaults.currency
  return merged
}

/** F9: posledné platné vstupy sa ukladajú do localStorage. Neplatný stav sa neukladá (F2). */
export function usePersistentForm(valid: (form: FormState) => boolean) {
  const [form, setForm] = useState<FormState>(restore)

  useEffect(() => {
    if (valid(form)) writeJson(KEYS.inputs, form)
  }, [form, valid])

  return [form, setForm] as const
}
