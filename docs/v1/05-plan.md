# 05 – Plán implementácie

Plán je rozdelený na fázy, ktoré zodpovedajú hodinám na vyučovaní (session = jedna hodina / jeden blok práce s Claude Code). Každá fáza končí funkčným, otestovaným stavom a zápisom do `docs/handoff.md`.

## Fáza 0 – Príprava (session 1)

- [x] Repozitár, `README.md`, `CLAUDE.md`, dokumentácia `docs/v1/01–05`
- [x] Kostra adresárov `frontend/`, `api/`, `supabase/`
- [x] `.gitignore`, `.env.example`, `.editorconfig`

**Hotovo, keď:** repo je na GitHube a dokumentácia je schválená.

## Fáza 1 – Výpočtová logika `calc` (session 2–3)

- [x] `models.py`, `validation.py` + testy V01–V09
- [x] `amortization.py` + testy C01–C11, C15–C16
- [x] `schedule.py`, `summary.py` + testy C08, C09, C12, C13
- [x] `export.py` + test C14
- [x] CLI `python -m calc`

**Hotovo, keď:** `pytest api/tests/calc` je zelený a CLI vypíše súhrn pre predvolené hodnoty.

## Fáza 2 – API bez databázy (session 4)

- [x] FastAPI app, `config.py`, CORS, `GZipMiddleware`
- [x] `/health`, `/calculate`, `/export/csv` + testy A01–A04, A07, A08, A20
- [x] Jednotný formát chýb `{errors: [...]}`

**Hotovo, keď:** `curl` na `/calculate` vráti C01 hodnoty.

## Fáza 3 – Supabase (session 5)

- [x] `supabase init`, migrácie `scenarios`, `calculation_log` (aplikované do cloudu cez Supabase MCP)
- [x] RLS zapnuté, bez politík; trigger `updated_at`; `pg_cron` retencia
- [x] pgTAP testy D01–D06
- [x] `db/` repozitáre v API + endpointy scenárov a zdieľania + testy A05, A06, A09–A19

**Hotovo, keď:** scenár sa dá cez `curl` vytvoriť, zdieľať a načítať cez slug.

## Fáza 4 – Frontend: kalkulačka (session 6–7)

- [x] Vite + React + TS, `api/client.ts`, typy podľa schém API
- [x] `LoanForm` (F1, F2), `parseNumber`, `validate` + testy F01, F04, F06
- [x] `useCalculation` (debounce, abort) + test F03, F05
- [x] `Summary`, `BreakdownBar` (F4)
- [x] Mena, téma, `localStorage` (F7–F9) + test F07

## Fáza 5 – Frontend: grafy, harmonogram (session 8)

- [x] `BalanceChart`, `YearlyChart` s prístupnými tooltipmi (F5) + test F09
- [x] `ScheduleTable` ročne/mesačne, *Stiahnuť CSV* (F6)

## Fáza 6 – Frontend: scenáre a zdieľanie (session 9)

- [ ] `clientId.ts`, `ScenarioList` (F11)
- [ ] Router, `ShareView` na `/s/:slug` (F12) + test F08

## Fáza 7 – Nasadenie a odovzdanie (session 10)

- [ ] Supabase projekt v cloude, `supabase db push`
- [ ] API na Render/Railway, frontend na Vercel/Netlify
- [ ] E2E checklist E01–E09
- [ ] `06-retro.md`

## Závislosti

```
Fáza 1 ──▶ Fáza 2 ──▶ Fáza 3 ──▶ Fáza 6
              │
              └──────▶ Fáza 4 ──▶ Fáza 5 ──▶ Fáza 7
```

Frontend (fáza 4) môže začať hneď po fáze 2 s lokálne bežiacim API.
