import { KEYS, readJson, writeJson } from './storage'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

let memoryId: string | null = null

/** Anonymný identifikátor prehliadača pre uložené scenáre (F9, F11). Nikdy sa nezobrazuje v UI. */
export function getClientId(): string {
  const stored = readJson<string>(KEYS.clientId)
  if (stored && UUID_RE.test(stored)) return stored
  memoryId ??= crypto.randomUUID()
  writeJson(KEYS.clientId, memoryId)
  return memoryId
}
