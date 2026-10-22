# Hypotekárna kalkulačka v2

Školský projekt, na ktorom pracujeme na vyučovaní. Webová aplikácia odhadne mesačnú splátku hypotéky, celkové úroky, dátum splatenia a vplyv mimoriadnych splátok. Varianty úveru sa dajú uložiť a zdieľať odkazom.

Projekt nadväzuje na prvú verziu (statická kalkulačka v prehliadači) a rozdeľuje ju na samostatný frontend, API, výpočtovú logiku a databázu. Vzniká postupne po hodinách s pomocou AI asistenta (Claude Code). Každý krok je zdokumentovaný, aby sa dal zopakovať a vyhodnotiť.

> **Stav:** fáza 0 – dokumentácia. Kód zatiaľ nie je implementovaný (pozri [plán](docs/v1/05-plan.md)).

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

## Spustenie (po implementácii)

```bash
# databáza (Docker)
supabase start && supabase db reset

# API
cd api && cp .env.example .env && uv sync && uv run uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev
```
