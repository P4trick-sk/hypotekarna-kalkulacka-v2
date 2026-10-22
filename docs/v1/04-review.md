# 04 – Review návrhu

Kritické posúdenie `01-functional.md` a `02-architecture.md` pred začatím implementácie. Každý bod má rozhodnutie; otvorené body sa riešia v `05-plan.md`.

## 1. Riziká a rozhodnutia

| # | Téma | Riziko | Rozhodnutie | Stav |
| --- | --- | --- | --- | --- |
| R1 | Výpočet presunutý z prehliadača na API | Živá odozva závisí od siete; pri výpadku API kalkulačka nefunguje (v1 fungovala offline) | Debounce 250 ms + `AbortController`; jasná hláška pri výpadku (AK 11). Offline režim je mimo rozsahu. | prijaté |
| R2 | `client_id` bez prihlásenia | Je to tajomstvo nositeľa; ak unikne (napr. pri zdieľaní obrazovky DevTools), cudzí človek vidí a maže scenáre | Nikdy ho nezobrazovať v UI ani v zdieľacom odkaze; `404` namiesto `403` pre cudzie scenáre. Prihlásenie zvážiť vo v2 dokumentácie. | prijaté |
| R3 | Strata scenárov | Vymazanie dát prehliadača = strata prístupu k scenárom | Vedomé obmedzenie, uvedené v F11 a v UI (tooltip pri „Moje scenáre“) | prijaté |
| R4 | Uhádnuteľnosť zdieľacieho odkazu | Krátky slug sa dá prehľadať | 10 znakov base62 ≈ 59 bitov, generované cez `secrets`; rate limit na `/share` | prijaté |
| R5 | Zneužitie API (spam scenárov, logu) | Plná DB na free tieri | Limit 50 scenárov na klienta, throttling logu (F13), jednoduchý rate limit (`slowapi`, 60 req/min/IP) | prijaté |
| R6 | `service_role` kľúč | Únik = plný prístup k DB | Len v env API, nikdy vo frontende ani v gite; `.env` v `.gitignore`, `.env.example` bez hodnôt | prijaté |
| R7 | Float vs. Decimal | Rozdiely v centoch medzi frontendom a API | Frontend nepočíta; sumy v JSON ako reťazce | prijaté |
| R8 | Zaokrúhľovanie poslednej splátky | Pri zaokrúhlenej splátke vzniká 361. mini-splátka | Podmienka `k == n` v algoritme; test C01 | prijaté |
| R9 | Osobné údaje v logu | GDPR | Log bez `client_id` a IP; retencia 90 dní | prijaté |
| R10 | Studený štart free hostingu API | Prvá požiadavka trvá 30+ s | Frontend pri štarte zavolá `/health` a zobrazí „Pripravujem kalkulačku…“ | otvorené |
| R11 | Veľkosť odpovede | 600 mesačných riadkov × každý úder klávesy | ~40 kB JSON, gzip cez `GZipMiddleware`; akceptovateľné | prijaté |
| R12 | Duplicitná validácia (TS aj Python) | Pravidlá sa rozídu | Zdroj pravdy je `calc.validation`; TS pravidlá sú kópia s rovnakými kódmi chýb a testami V01–V09 na oboch stranách | prijaté |

## 2. Otvorené otázky

- **Q1:** Má zdieľaný scenár ukázať aj názov scenára? *Návrh: áno, názov zadal vlastník vedome.*
- **Q2:** Má sa pri načítaní scenára prepísať aj mena? *Návrh: áno.*
- **Q3:** Ukladať do logu aj neúspešné (`422`) výpočty pre analýzu častých chýb? *Návrh: nie v iterácii v1.*
- **Q4:** Hosting API – Render vs. Railway (studený štart vs. cena). Rozhodne sa pri nasadení.

## 3. Checklist kvality pred mergom

- [ ] Všetky testy `pytest` a `vitest` prechádzajú.
- [ ] `ruff` + `mypy --strict` pre `api/`, `eslint` + `tsc --noEmit` pre `frontend/`.
- [ ] Nová migrácia má aj test v `supabase/tests/`.
- [ ] Žiadny kľúč ani `.env` v diffe.
- [ ] Dokumentácia (`01`–`03`) zodpovedá implementácii.
