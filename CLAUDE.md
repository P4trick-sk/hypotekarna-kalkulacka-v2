# CLAUDE.md

Inštrukcie pre Claude Code v tomto repozitári.

## Projekt

Hypotekárna kalkulačka v2: školský projekt, na ktorom pracujeme na vyučovaní po session (hodinách). Monorepo so štyrmi časťami:

- `frontend/` – React + Vite + TypeScript
- `api/app/` – FastAPI (HTTP vrstva, Pydantic schémy, prístup k DB)
- `api/calc/` – vlastné Python skripty s výpočtovou logikou (čistý Python, len štandardná knižnica)
- `supabase/` – migrácie a testy databázy

Zdroj pravdy o tom, čo stavať: `docs/v1/01-functional.md` (čo), `docs/v1/02-architecture.md` (ako), `docs/v1/03-test-scenarios.md` (overenie), `docs/v1/05-plan.md` (poradie).

## Začiatok session

1. Prečítaj `docs/handoff.md`.
2. Zhrň stav a navrhni ďalší krok podľa `docs/v1/05-plan.md`.
3. Počkaj na potvrdenie a až potom začni meniť kód.

## Koniec session (`/end-session`)

1. Aktualizuj `docs/handoff.md`: hotovo / rozpracované / ďalší krok / otvorené otázky.
2. Pridaj použité prompty do `docs/v1/prompts.md`.
3. Odškrtni hotové body v `docs/v1/05-plan.md`.
4. Navrhni commit správu (commit urob len na požiadanie).

## Pravidlá

- **Výpočty len v `api/calc/`.** Frontend nepočíta sumy; API len volá `calc`.
- `calc` nesmie importovať FastAPI, Pydantic ani Supabase.
- Peniaze: `Decimal` v Pythone, `numeric(14,2)` v DB, reťazce v JSON. Nikdy `float`.
- Frontend nevolá Supabase priamo a nemá žiadny Supabase kľúč.
- `SUPABASE_SERVICE_ROLE_KEY` nikdy nepatrí do gitu ani do frontendu.
- Každá zmena schémy DB = nová migrácia v `supabase/migrations/`, nikdy úprava starej.
- Testy píš podľa ID z `03-test-scenarios.md` (`test_C01_...`, `test_A12_...`).
- Pri zmene správania najprv uprav dokumentáciu v `docs/v1/`, potom kód.
- Dokumentácia a UI texty po slovensky; identifikátory v kóde po anglicky.

## Príkazy

```bash
# API + calc
cd api && uv sync
uv run pytest
uv run ruff check . && uv run mypy --strict app calc
uv run uvicorn app.main:app --reload
uv run python -m calc --price 300000 --down 60000 --rate 4.5 --years 30

# Frontend
cd frontend && npm install
npm run dev
npm test
npm run lint && npx tsc --noEmit

# Supabase (lokálne, vyžaduje Docker)
supabase start
supabase db reset        # aplikuje migrácie
supabase test db
```
