# Hypotekárna kalkulačka v2

Školský projekt, na ktorom pracujeme na vyučovaní. Webová aplikácia odhadne mesačnú splátku hypotéky, celkové úroky, dátum splatenia a vplyv mimoriadnych splátok. Varianty úveru sa dajú uložiť a zdieľať odkazom.

Projekt nadväzuje na prvú verziu (statická kalkulačka v prehliadači) a rozdeľuje ju na samostatný frontend, API, výpočtovú logiku a databázu. Vzniká postupne po hodinách s pomocou AI asistenta (Claude Code). Každý krok je zdokumentovaný, aby sa dal zopakovať a vyhodnotiť.

> **Stav:** fázy 0–6 hotové, aplikácia beží lokálne napojená na Supabase. Zostáva fáza 7 (E2E checklist, retrospektíva) – pozri [plán](docs/v1/05-plan.md).

## Architektúra

```
React (frontend)  ──HTTP/JSON──▶  FastAPI (api/app)  ──▶  Supabase (PostgreSQL)
                                       │
                                       ▼
                               vlastné Python skripty
                                    (api/calc)
```

| Časť | Technológia | Čo robí |
| --- | --- | --- |
| `frontend/` | React, Vite, TypeScript, Recharts | Formulár, grafy, amortizačná tabuľka, téma, lokálne uloženie |
| `api/app/` | FastAPI, Pydantic | REST API `/api/v1`, validácia, scenáre, zdieľanie |
| `api/calc/` | Python (štandardná knižnica) | Anuitný výpočet, harmonogram, porovnanie, CSV |
| `supabase/` | Supabase / PostgreSQL | Uložené scenáre, zdieľacie odkazy, log výpočtov |

## Funkcie

- Výpočet mesačnej splátky (istina + úrok, daň, poistenie) s okamžitou aktualizáciou
- Mimoriadne splátky: o koľko skôr a koľko sa ušetrí
- Grafy zostatku a pomeru istina/úrok, ročný a mesačný harmonogram, export do CSV
- 6 mien, svetlá/tmavá téma, prístupnosť z klávesnice, responzívne rozloženie
- Uloženie scenárov bez registrácie, zdieľanie odkazom len na čítanie

## Dokumentácia

| Dokument | Obsah |
| --- | --- |
| [01 – Funkčná špecifikácia](docs/v1/01-functional.md) | Čo aplikácia robí, akceptačné kritériá |
| [02 – Architektúra](docs/v1/02-architecture.md) | Vrstvy, API, výpočtový algoritmus, DB schéma |
| [03 – Testovacie scenáre](docs/v1/03-test-scenarios.md) | Golden values, testy API, DB, frontendu, E2E |
| [04 – Review](docs/v1/04-review.md) | Riziká, rozhodnutia, otvorené otázky |
| [05 – Plán](docs/v1/05-plan.md) | Fázy po session |
| [06 – Retrospektíva](docs/v1/06-retro.md) | Vyhodnotenie iterácie |
| [Prompty](docs/v1/prompts.md) | Záznam práce s AI |
| [Handoff](docs/handoff.md) | Prenos kontextu medzi session |

## Ako pracujeme na hodinách

1. **Začiatok hodiny:** Claude Code prečíta [`CLAUDE.md`](CLAUDE.md) a [`docs/handoff.md`](docs/handoff.md) a zhrnie, kde sme skončili.
2. **Práca:** jedna fáza z plánu; testy podľa ID z `03-test-scenarios.md` sa píšu pred implementáciou.
3. **Koniec hodiny:** `/end-session` aktualizuje handoff a zapíše prompty.
4. **Koniec iterácie:** retrospektíva v `06-retro.md`; ďalšia iterácia dostane priečinok `docs/v2/`.

## Spustenie lokálne

Predpoklady: Python 3.12 cez [uv](https://docs.astral.sh/uv/), Node.js 20+.

```bash
# 1. API (http://localhost:8000, dokumentácia na /docs)
cd api
cp .env.example .env          # doplň DATABASE_URL, pozri nižšie
uv sync
uv run uvicorn app.main:app --reload

# 2. frontend (http://localhost:5173, /api ide cez Vite proxy na port 8000)
cd frontend
npm install
npm run dev
```

Bez `DATABASE_URL` funguje výpočet, grafy aj CSV; ukladanie a zdieľanie scenárov hlási „nedostupné“.

## Pripojenie k Supabase

API sa nepripája `service_role` kľúčom, ale vlastnou Postgres rolou `hk_api`, ktorá smie len do tabuliek kalkulačky (migrácia [`api_role`](supabase/migrations/20261022072603_api_role.sql)).

1. Aplikuj migrácie zo `supabase/migrations/` (cez Supabase MCP `apply_migration` alebo `supabase db push`).
2. Vygeneruj heslo a jeho SCRAM hash **lokálne** (do Supabase ide len hash):
   ```bash
   python3 -c "import secrets,hashlib,hmac,base64 as b;p=secrets.token_urlsafe(32);s=secrets.token_bytes(16);k=hashlib.pbkdf2_hmac('sha256',p.encode(),s,4096);c=hmac.new(k,b'Client Key','sha256').digest();print('heslo:',p);print(f\"SCRAM-SHA-256\$4096:{b.b64encode(s).decode()}\${b.b64encode(hashlib.sha256(c).digest()).decode()}:{b.b64encode(hmac.new(k,b'Server Key','sha256').digest()).decode()}\")"
   ```
3. V SQL editore (alebo cez MCP `execute_sql`): `alter role hk_api with login password '<SCRAM hash>' connection limit 10;`
4. Do `api/.env`:
   ```
   DATABASE_URL=postgresql://hk_api.<project-ref>:<heslo>@aws-1-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require
   ```
   Priame pripojenie `db.<ref>.supabase.co` je len cez IPv6, preto sa používa pooler (IPv4, session mód).
5. Over: `cd api && uv run pytest -m integration`.

## Testy

```bash
cd api && uv run pytest                  # 74 unit testov (calc + API)
cd api && uv run pytest -m integration   # životný cyklus scenára proti skutočnej DB
cd frontend && npm test                  # 44 testov (Vitest + Testing Library)
```
