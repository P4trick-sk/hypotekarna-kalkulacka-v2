// localStorage môže hádzať výnimky (súkromné okno, zablokované dáta) – aplikácia musí fungovať aj tak.

export function readJson<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? null : (JSON.parse(raw) as T)
  } catch {
    return null
  }
}

export function writeJson(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // ignorujeme – stav sa len nezapamätá
  }
}

export const KEYS = {
  inputs: 'hk.inputs',
  theme: 'hk.theme',
  clientId: 'hk.clientId',
} as const
