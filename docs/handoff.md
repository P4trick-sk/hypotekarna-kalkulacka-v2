# Handoff

Prenos kontextu medzi session (hodinami). Aktualizuje sa na konci každej session príkazom `/end-session`. Nová session začína prečítaním tohto súboru.

---

## Posledná session: 2026-10-22 – Fáza 0 (dokumentácia)

### Hotovo
- Repozitár založený a pushnutý na GitHub.
- Dokumentácia `docs/v1/01-functional.md` až `05-plan.md`; `06-retro.md` je šablóna.
- Architektúra: React (frontend) → FastAPI (API) → vlastný Python balík `calc` (výpočty) → Supabase (scenáre, zdieľanie, log).
- Golden values pre testy výpočtov (C01–C05) overené referenčným skriptom.

### Rozpracované
- Nič.

### Ďalší krok
- **Fáza 1** z `05-plan.md`: kostra `api/calc/`, `models.py` a `validation.py` s testami V01–V09.

### Otvorené otázky
- Q1–Q4 v `docs/v1/04-review.md`.
- R10 (studený štart hostingu API).

### Poznámky pre ďalšiu session
- Kód zatiaľ neexistuje, len dokumentácia.
- Pôvodná (anglická) špecifikácia statickej v1 je v prvom commite repozitára.
