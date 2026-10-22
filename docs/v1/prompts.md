# Prompty

Záznam dôležitých promptov použitých pri práci s Claude Code. Slúži na reprodukovateľnosť a na retrospektívu (`06-retro.md`).

Formát záznamu:

```
## <dátum> – <fáza> – <krátky názov>
**Prompt:** ...
**Výsledok:** čo vzniklo (súbory, commit)
**Poznámka:** čo bolo treba opraviť / čo sa osvedčilo
```

---

## 2026-10-22 – Fáza 0 – Technická dokumentácia

**Prompt:**
> from this functionality.md create a tech doc for the calculator with the following structure (README.md, CLAUDE.md, docs/handoff.md, docs/v1/01-functional.md … 06-retro.md, prompts.md). It shall be divided into frontend react, api, python calc logic and supabase for database. Create a git repo from this, push it, describe it as a project from that we work in classroom. Ask me details about the app.

**Upresnenia (odpovede na otázky):**
- jazyk dokumentácie: slovenčina
- API: FastAPI + vlastné Python skripty
- Supabase: uložené scenáre, zdieľacie odkazy, log výpočtov (bez prihlásenia)
- repo: verejné, samostatný projekt

**Výsledok:** dokumentácia `docs/v1/01–06`, `README.md`, `CLAUDE.md`, `docs/handoff.md`; verejné repo na GitHube.

**Poznámka:** Pôvodná anglická špecifikácia statickej verzie je zachovaná v prvom commite.

---

## Šablóny promptov pre ďalšie fázy

### Začiatok session
> Prečítaj `CLAUDE.md` a `docs/handoff.md`. Pokračujeme fázou X z `docs/v1/05-plan.md`. Najprv mi zhrň, čo je hotové a čo je ďalší krok.

### Implementácia s testami
> Implementuj `<modul>` podľa `docs/v1/02-architecture.md`, sekcia <N>. Najprv napíš testy <ID> z `03-test-scenarios.md`, spusti ich (majú zlyhať), potom implementáciu. Nemeň verejné rozhranie bez úpravy dokumentácie.

### Review
> Urob review zmien v tejto session voči `docs/v1/04-review.md` (checklist kvality). Vypíš len skutočné problémy.

### Koniec session
> /end-session – aktualizuj `docs/handoff.md` (hotovo, rozpracované, ďalší krok, otvorené otázky) a pridaj použité prompty do `docs/v1/prompts.md`.
