# 02 – Architektúra

## 1. Prehľad

```
┌────────────────────────┐   HTTPS / JSON   ┌──────────────────────────────┐   PostgREST / SQL   ┌──────────────────┐
│  Frontend (React)      │ ───────────────▶ │  API (FastAPI)               │ ──────────────────▶ │  Supabase        │
│  Vite + TypeScript     │ ◀─────────────── │  ├─ routers/   (HTTP vrstva) │ ◀────────────────── │  PostgreSQL      │
│  - vstupy, validácia   │                  │  ├─ schemas/   (Pydantic)    │                     │  - scenarios     │
│  - grafy, tabuľka      │                  │  ├─ db/        (Supabase)    │                     │  - calculation_  │
│  - localStorage        │                  │  └─ calc/      (čistý Python)│                     │    log           │
└────────────────────────┘                  └──────────────────────────────┘                     └──────────────────┘
```

Zásady:

1. **Výpočet je len v Pythone.** Frontend nič nepočíta okrem parsovania čísel a validácie pre UX.
2. **`calc` je čistý Python.** Žiadne I/O, žiadny FastAPI, žiadna databáza. Vstup = dataclass, výstup = dataclass. Dá sa spustiť a testovať samostatne.
3. **Frontend nikdy nehovorí so Supabase priamo.** Všetok prístup k dátam ide cez API, ktoré drží `service_role` kľúč. V prehliadači nie je žiadny Supabase kľúč.
4. **Peniaze sú `Decimal`** v Pythone a `numeric(14,2)` v databáze. V JSON sa posielajú ako reťazce (`"1216.04"`), aby sa nestratila presnosť.

## 2. Štruktúra repozitára (cieľová)

```
hypotekarna-kalkulacka-v2/
├── README.md
├── CLAUDE.md
├── docs/
│   ├── handoff.md
│   └── v1/ ...
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/            client.ts, types.ts
│       ├── components/     LoanForm, Summary, BreakdownBar, BalanceChart,
│       │                   YearlyChart, ScheduleTable, ScenarioList, ShareView
│       ├── hooks/          useCalculation.ts (debounce + abort), usePersistentState.ts
│       ├── lib/            parseNumber.ts, format.ts, validate.ts, clientId.ts
│       └── styles/
├── api/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py         FastAPI app, CORS, routery
│   │   ├── config.py       nastavenia z env (pydantic-settings)
│   │   ├── routers/        calculate.py, export.py, scenarios.py, share.py, health.py
│   │   ├── schemas/        loan.py, result.py, scenario.py, errors.py
│   │   └── db/             client.py, scenarios_repo.py, log_repo.py
│   ├── calc/               vlastné Python skripty – výpočtová logika
│   │   ├── __init__.py
│   │   ├── models.py       LoanInput, Payment, ScheduleResult (dataclasses)
│   │   ├── validation.py   validate(LoanInput) -> list[ValidationError]
│   │   ├── amortization.py monthly_payment(), build_schedule()
│   │   ├── schedule.py     yearly_rollup(), compare(), sooner_text()
│   │   ├── summary.py      summary(), calculate()
│   │   ├── export.py       to_csv()
│   │   └── __main__.py     CLI: python -m calc --price 300000 ...
│   └── tests/
│       ├── calc/           unit testy výpočtov (golden values)
│       └── api/            testy endpointov (TestClient, fake repo)
└── supabase/
    ├── config.toml
    └── migrations/
        ├── 0001_scenarios.sql
        └── 0002_calculation_log.sql
```

## 3. Frontend (React)

| Oblasť | Rozhodnutie |
| --- | --- |
| Build | Vite + TypeScript (strict) |
| Stav | Lokálny stav v `App` + vlastné hooky, bez Reduxu |
| Grafy | Recharts (tooltipy z klávesnice doplnené vlastným `onKeyDown`) |
| Routing | React Router: `/` kalkulačka, `/s/:slug` zdieľaný scenár |
| Volanie API | `fetch` cez `api/client.ts`; `useCalculation` robí debounce 250 ms a ruší starú požiadavku cez `AbortController` |
| Perzistencia | `localStorage`: `hk.inputs`, `hk.currency`, `hk.theme`, `hk.clientId` (všetko v `try/catch`) |
| Formátovanie | `Intl.NumberFormat`, `Intl.DateTimeFormat` podľa jazyka prehliadača |
| Konfigurácia | `VITE_API_URL` |

Tok pri zmene vstupu:

1. Vstup → `parseNumber` → `validate` (frontend).
2. Neplatné → zobraz chybu, výsledky stlm, koniec.
3. Platné → ulož do `localStorage` → po 250 ms `POST /api/v1/calculate`.
4. Odpoveď `200` → vykresli. `422` → zobraz chybu z API. Sieťová chyba / `5xx` → hláška „Výpočet je dočasne nedostupný“, výsledky stlm.

## 4. API (FastAPI)

Prefix `/api/v1`. Všetky telá sú JSON, sumy sú reťazce s dvoma desatinnými miestami.

| Metóda | Cesta | Popis | Hlavičky |
| --- | --- | --- | --- |
| `GET` | `/health` | `{"status":"ok","db":"ok"}` | – |
| `POST` | `/calculate` | Súhrn + mesačný a ročný harmonogram + porovnanie bez mimoriadnej splátky | `X-Log: 0/1` |
| `POST` | `/export/csv` | Rovnaký vstup ako `/calculate`, vráti `text/csv` s `Content-Disposition` | – |
| `GET` | `/scenarios` | Zoznam scenárov aktuálneho klienta | `X-Client-Id` |
| `POST` | `/scenarios` | Vytvorí scenár `{name, inputs, currency}` | `X-Client-Id` |
| `GET` | `/scenarios/{id}` | Detail scenára | `X-Client-Id` |
| `PATCH` | `/scenarios/{id}` | Premenovanie a/alebo prepísanie vstupov | `X-Client-Id` |
| `DELETE` | `/scenarios/{id}` | Zmazanie | `X-Client-Id` |
| `POST` | `/scenarios/{id}/share` | Zapne zdieľanie, vráti `{slug, url}` | `X-Client-Id` |
| `DELETE` | `/scenarios/{id}/share` | Zruší zdieľanie | `X-Client-Id` |
| `GET` | `/share/{slug}` | Verejný scenár len na čítanie + výsledok výpočtu | – |

### Vstup výpočtu (`LoanInput`)

```json
{
  "price": "300000.00",
  "down_payment": "60000.00",
  "annual_rate": "4.5",
  "term_years": 30,
  "first_payment": "2026-11",
  "extra_monthly": "0.00",
  "tax_yearly": "1200.00",
  "insurance_yearly": "600.00",
  "currency": "EUR"
}
```

### Výstup výpočtu (skrátene)

```json
{
  "summary": {
    "loan_amount": "240000.00",
    "down_payment_pct": "20.00",
    "ltv_pct": "80.00",
    "monthly_pi": "1216.04",
    "monthly_extra": "0.00",
    "monthly_escrow": "150.00",
    "monthly_total": "1366.04",
    "total_interest": "197778.11",
    "total_cost": "437778.11",
    "payoff_date": "2056-10",
    "payments_count": 360,
    "baseline": null
  },
  "monthly": [{"n": 1, "date": "2026-11", "payment": "1216.04", "principal": "316.04", "interest": "900.00", "balance": "239683.96"}],
  "yearly":  [{"year": 2026, "payment": "...", "principal": "...", "interest": "...", "balance": "..."}]
}
```

`baseline` je vyplnený len pri `extra_monthly > 0`: `{payments_count, total_interest, interest_saved, months_sooner}` a `baseline_balance` (zostatok bez mimoriadnej splátky po mesiacoch, pre graf).

### Chyby

```json
{ "errors": [ { "field": "down_payment", "code": "gte_price", "message": "Akontácia musí byť nižšia ako cena nehnuteľnosti." } ] }
```

| Kód | Kedy |
| --- | --- |
| `422` | Neplatný vstup (Pydantic alebo `calc.validation`) |
| `400` | Chýbajúca alebo neplatná `X-Client-Id` (nie UUID) |
| `404` | Scenár neexistuje **alebo** nepatrí klientovi (zámerne rovnaká odpoveď); zrušený zdieľací odkaz |
| `409` | Prekročený limit 50 scenárov |
| `503` | Databáza nedostupná (výpočet `/calculate` funguje aj bez DB) |

### Vrstvy

- `routers/` – len HTTP: parsovanie, hlavičky, mapovanie chýb na status kódy.
- `schemas/` – Pydantic modely; konverzia na `calc.models` cez `to_domain()`.
- `calc/` – čistá logika (pozri 5).
- `db/` – jediné miesto, kde sa volá Supabase (`supabase-py`, `service_role` kľúč). Repozitáre sú injektované cez `Depends`, v testoch sa nahrádzajú fake implementáciou.
- Log výpočtu sa zapisuje cez `BackgroundTasks`, aby nespomalil odpoveď; výnimky sa iba zalogujú.

### Konfigurácia (env)

| Premenná | Popis |
| --- | --- |
| `SUPABASE_URL` | URL projektu |
| `SUPABASE_SERVICE_ROLE_KEY` | Tajný kľúč, **len** na serveri |
| `CORS_ORIGINS` | Čiarkou oddelené povolené originy frontendu |
| `PUBLIC_APP_URL` | Základ pre zdieľacie odkazy |
| `CALC_LOG_ENABLED` | `true`/`false` |

## 5. Výpočtová logika (`api/calc/`)

Vlastné Python skripty bez externých závislostí (len štandardná knižnica: `decimal`, `dataclasses`, `datetime`, `csv`).

| Modul | Funkcia | Popis |
| --- | --- | --- |
| `models.py` | `LoanInput`, `Payment`, `ScheduleResult`, `Summary` | Nemenné dataclasses (`frozen=True`) |
| `validation.py` | `validate(inp) -> list[ValidationError]` | Pravidlá z F1; vracia všetky chyby v poradí polí |
| `amortization.py` | `monthly_payment(P, annual_rate, n)` | Anuitný vzorec, 0 % → `P / n`; zaokrúhlenie na centy |
| | `build_schedule(inp, extra=None)` | Mesačné riadky; posledná splátka = zvyšný zostatok |
| `schedule.py` | `yearly_rollup(rows)` | Súčty po kalendárnych rokoch |
| | `compare(with_extra, baseline)` | Ušetrené úroky, počet mesiacov skôr |
| | `sooner_text(months)` | „o 7 rokov a 6 mesiacov skôr“ (slovenské skloňovanie) |
| `summary.py` | `summary(inp, result)` | Polia pre F4 |
| | `calculate(inp)` | Celý výpočet: harmonogram, súhrn, ročný prehľad, porovnanie |
| `export.py` | `to_csv(rows) -> str` | Hlavička: `payment_no,date,payment,principal,interest,balance` |
| `__main__.py` | CLI | `python -m calc --price 300000 --down 60000 --rate 4.5 --years 30 [--extra 200] [--csv]` |

Algoritmus `build_schedule`:

```
r   = annual_rate / 100 / 12
pmt = monthly_payment(P, annual_rate, n)
bal = P
for k in 1..:
    interest  = round2(bal * r)
    principal = pmt - interest + extra
    if principal >= bal or k == n:      # posledná splátka
        principal = bal
    bal -= principal
    emit(k, date(k), principal + interest, principal, interest, bal)
    if bal == 0: break
```

Podmienka `k == n` zabezpečí, že rozdiel zo zaokrúhlenia splátky nevytvorí 361. splátku pri 30-ročnom úvere.

## 6. Databáza (Supabase)

### `scenarios`

| Stĺpec | Typ | Poznámka |
| --- | --- | --- |
| `id` | `uuid` PK | `default gen_random_uuid()` |
| `client_id` | `uuid not null` | Anonymný identifikátor prehliadača; index |
| `name` | `text not null` | `check (char_length(name) between 1 and 100)` |
| `inputs` | `jsonb not null` | `LoanInput` bez meny |
| `currency` | `char(3) not null` | `check (currency in ('EUR','USD','GBP','CZK','CHF','PLN'))` |
| `share_slug` | `text unique` | `null` = nezdieľané |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | trigger `set_updated_at` |

### `calculation_log`

| Stĺpec | Typ | Poznámka |
| --- | --- | --- |
| `id` | `bigint generated always as identity` PK | |
| `created_at` | `timestamptz not null default now()` | index pre mazanie |
| `source` | `text not null` | `check (source in ('live','scenario','share'))` |
| `inputs` | `jsonb not null` | |
| `monthly_total` | `numeric(14,2) not null` | |
| `total_interest` | `numeric(14,2) not null` | |
| `payments_count` | `int not null` | |
| `duration_ms` | `int not null` | |

Retencia: `pg_cron` úloha raz denne `delete from calculation_log where created_at < now() - interval '90 days'`.

### Bezpečnosť

- RLS je **zapnuté** na oboch tabuľkách a **nie sú** definované žiadne politiky pre `anon` ani `authenticated`. Prístup má len `service_role` (API).
- Vlastníctvo scenára kontroluje API: každý dotaz na `scenarios` obsahuje `where client_id = :client_id`.
- `client_id` je fakticky tajomstvo nositeľa (bearer). Kto ho pozná, vidí scenáre daného prehliadača. Rizikom sa zaoberá `04-review.md`.

## 7. Nasadenie (návrh)

| Časť | Kde | Poznámka |
| --- | --- | --- |
| Frontend | Vercel alebo Netlify | Statický build, SPA fallback pre `/s/:slug` |
| API | Render / Railway / Fly.io | `uvicorn app.main:app`, Python 3.12 |
| DB | Supabase (free tier) | Migrácie cez `supabase db push` |

Lokálny vývoj: `supabase start` (Docker), `uvicorn --reload` v `api/`, `npm run dev` vo `frontend/`.
