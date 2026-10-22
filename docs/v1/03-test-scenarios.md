# 03 – Testovacie scenáre

Testy sú rozdelené podľa vrstiev. Každý scenár má ID, ktoré sa uvádza v názve testu (napr. `test_C01_standard_30y`).

| Vrstva | Nástroj | Kde |
| --- | --- | --- |
| Výpočtová logika | `pytest` | `api/tests/calc/` |
| API | `pytest` + `fastapi.testclient` + fake repozitáre | `api/tests/api/` |
| Databáza | SQL testy cez `supabase test db` (pgTAP) | `supabase/tests/` |
| Frontend | Vitest + React Testing Library | `frontend/src/**/*.test.tsx` |
| End-to-end | Playwright (manuálne alebo v CI) | `frontend/e2e/` |

## 1. Výpočtová logika (`calc`) – golden values

Spoločné: prvá splátka `2026-11`, daň a poistenie 0, ak nie je uvedené inak. Hodnoty sú overené referenčnou implementáciou algoritmu z `02-architecture.md` (Decimal, ROUND_HALF_UP na centy).

| ID | Úver | Sadzba | Doba | Mimoriadna | Očakávaná splátka | Celkové úroky | Počet splátok | Posledná splátka |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | 240 000 | 4,5 % | 30 r | 0 | 1 216,04 | 197 778,11 | 360 | 1 219,75 |
| C02 | 240 000 | 4,5 % | 30 r | 200 | 1 216,04 | 141 888,39 | 270 | 973,63 |
| C03 | 120 000 | 0 % | 10 r | 0 | 1 000,00 | 0,00 | 120 | 1 000,00 |
| C04 | 100 000 | 3 % | 20 r | 0 | 554,60 | 33 103,24 | 240 | 553,84 |
| C05 | 240 000 | 4,5 % | 30 r | 3 000 | 1 216,04 | 30 473,97 | 65 | 647,41 |

Ďalšie kontroly:

| ID | Scenár | Očakávanie |
| --- | --- | --- |
| C06 | C01 – prvý riadok | úrok 900,00; istina 316,04; zostatok 239 683,96 |
| C07 | C01 – dátum splatenia | `2056-10` |
| C08 | C02 vs. C01 – porovnanie | ušetrené 55 889,72; o 90 mesiacov skôr („o 7 rokov a 6 mesiacov skôr“) |
| C09 | C05 vs. C01 | o 295 mesiacov skôr („o 24 rokov a 7 mesiacov skôr“) |
| C10 | Každý scenár | posledný zostatok = 0,00; súčet istín = výška úveru |
| C11 | Každý scenár | žiadny riadok nemá zápornú istinu ani zostatok |
| C12 | Daň 1 200, poistenie 600 | `monthly_escrow` = 150,00; harmonogram rovnaký ako bez nich |
| C13 | `yearly_rollup` pre C01 | prvý rok 2026 má 2 splátky (nov, dec), posledný 2056 má 10 |
| C14 | `to_csv` pre C03 | 121 riadkov (hlavička + 120), hlavička presne `payment_no,date,payment,principal,interest,balance` |
| C15 | Doba 1 rok, sadzba 50 % | výpočet prebehne, 12 splátok, zostatok 0 |
| C16 | Doba 50 rokov, cena 2 000 000 | výpočet do 200 ms |

## 2. Validácia (`calc.validation`)

| ID | Vstup | Pole | Kód |
| --- | --- | --- | --- |
| V01 | cena 0 | `price` | `gt_zero` |
| V02 | akontácia = cena | `down_payment` | `gte_price` |
| V03 | akontácia −1 | `down_payment` | `negative` |
| V04 | sadzba 50,01 | `annual_rate` | `out_of_range` |
| V05 | doba 0 / 51 / 12,5 | `term_years` | `out_of_range` / `out_of_range` / `not_integer` |
| V06 | mimoriadna −10 | `extra_monthly` | `negative` |
| V07 | mena `JPY` | `currency` | `unsupported` |
| V08 | viac chýb naraz (cena 0, sadzba 60) | – | vráti obe, v poradí polí z F1 |
| V09 | `first_payment` = `2026-13` | `first_payment` | `invalid_date` |

## 3. API

| ID | Požiadavka | Očakávanie |
| --- | --- | --- |
| A01 | `GET /health` | `200`, `status: ok` |
| A02 | `POST /calculate` s predvolenými hodnotami | `200`, `summary.monthly_total = "1366.04"`, 360 riadkov `monthly` |
| A03 | `POST /calculate` s V02 | `422`, `errors[0].code = "gte_price"` |
| A04 | `POST /calculate` – sumy sú reťazce | žiadne float hodnoty v odpovedi |
| A05 | `POST /calculate` s `X-Log: 1` | fake log repo dostane 1 záznam bez `client_id` |
| A06 | `POST /calculate`, log repo vyhodí výnimku | `200`, výsledok nezmenený |
| A07 | `POST /calculate`, DB nedostupná | `200` (výpočet nezávisí od DB) |
| A08 | `POST /export/csv` | `text/csv`, `Content-Disposition: attachment; filename="mortgage-schedule-eur.csv"` |
| A09 | `GET /scenarios` bez `X-Client-Id` | `400` |
| A10 | `GET /scenarios` s `X-Client-Id: abc` | `400` |
| A11 | `POST /scenarios` + `GET /scenarios` | scenár je v zozname |
| A12 | `GET /scenarios/{id}` s cudzím `client_id` | `404` |
| A13 | `DELETE /scenarios/{id}` s cudzím `client_id` | `404`, scenár stále existuje |
| A14 | 51. scenár | `409` |
| A15 | `POST /scenarios` s neplatnými vstupmi | `422`, nič sa neuloží |
| A16 | `POST /scenarios/{id}/share` | `200`, `slug` má 10 znakov `[A-Za-z0-9]` |
| A17 | `GET /share/{slug}` | `200`, odpoveď neobsahuje `client_id` ani `id` |
| A18 | `DELETE /scenarios/{id}/share` + `GET /share/{slug}` | `404` |
| A19 | `POST /scenarios/{id}/share` dvakrát | rovnaký `slug` (idempotentné) |
| A20 | CORS z nepovoleného originu | bez hlavičky `Access-Control-Allow-Origin` |

## 4. Databáza

| ID | Scenár | Očakávanie |
| --- | --- | --- |
| D01 | `select` z `scenarios` ako rola `anon` | `permission denied` (RLS + `revoke`) |
| D02 | `insert` do `calculation_log` ako `anon` | zamietnuté |
| D03 | `name` dlhé 101 znakov | porušenie `check` |
| D04 | dva scenáre s rovnakým `share_slug` | porušenie `unique` |
| D05 | `update` scenára | `updated_at` sa zmení |
| D06 | Retenčná úloha | záznam starší ako 90 dní zmizne, novší zostane |

## 5. Frontend

| ID | Scenár | Očakávanie |
| --- | --- | --- |
| F01 | `parseNumber("250,000.50")` a `parseNumber("250 000,50")` | `250000.5` |
| F02 | Prvé načítanie (mock API) | zobrazí výsledky predvolených hodnôt |
| F03 | Rýchle písanie 5 znakov | najviac 1 požiadavka po debounce, staršie zrušené |
| F04 | Akontácia > cena | chybová hláška s `role="alert"`, výsledky majú `aria-busy`/stlmený stav, žiadna požiadavka |
| F05 | API vráti `503` | hláška „Výpočet je dočasne nedostupný“ |
| F06 | Zmena akontácie v % | suma sa prepočíta a naopak |
| F07 | `localStorage` hádže výnimku | aplikácia funguje, len si nepamätá stav |
| F08 | `/s/:slug` | formulár je len na čítanie, tlačidlo *Otvoriť v kalkulačke* |
| F09 | Klávesnica: Tab cez všetky prvky, šípky v grafe | tooltip sa presúva po bodoch |

## 6. End-to-end (manuálny checklist pred odovzdaním)

- [ ] E01 Predvolené hodnoty → mesačná splátka 1 366,04 € (sk-SK formát).
- [ ] E02 Mimoriadna splátka 200 → odznak „o 7 rokov a 6 mesiacov skôr“.
- [ ] E03 Uložiť scenár „Byt Košice“ → obnoviť stránku → scenár je v zozname.
- [ ] E04 Zdieľať → otvoriť odkaz v anonymnom okne → rovnaké čísla, len na čítanie.
- [ ] E05 Zrušiť zdieľanie → odkaz zobrazí „Odkaz už neplatí“.
- [ ] E06 Stiahnuť CSV → otvoriť v tabuľkovom editore, 360 riadkov.
- [ ] E07 Vypnúť API → hláška o nedostupnosti, stránka nespadne.
- [ ] E08 Mobil 375 px → bez horizontálneho posúvania.
- [ ] E09 Tmavá téma → grafy čitateľné, voľba sa zapamätá.
