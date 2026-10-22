# 01 – Funkčná špecifikácia

> Verzia dokumentu: v1 (prvá iterácia projektu `hypotekarna-kalkulacka-v2`)
> Zdroj: pôvodná špecifikácia statickej kalkulačky (pozri git históriu, commit „Pôvodná funkčná špecifikácia v1“), rozšírená o backend, ukladanie scenárov a zdieľanie.

## 1. Účel

Hypotekárna kalkulačka odhadne, koľko bude stáť úver na bývanie: mesačnú splátku, celkové úroky, dátum splatenia a vplyv mimoriadnych splátok.

Oproti pôvodnej verzii (čisto statická stránka v prehliadači) je v2 rozdelená na štyri časti:

| Časť | Technológia | Zodpovednosť |
| --- | --- | --- |
| Frontend | React (Vite, TypeScript) | Vstupy, validácia pre UX, zobrazenie výsledkov, grafy, tabuľka |
| API | FastAPI (Python) | HTTP rozhranie, autoritatívna validácia, prístup k databáze |
| Výpočtová logika | Vlastné Python skripty (balík `calc`) | Amortizácia, harmonogram, porovnanie, CSV export |
| Databáza | Supabase (PostgreSQL) | Uložené scenáre, zdieľacie odkazy, log výpočtov |

Používateľ sa **neprihlasuje**. Uložené scenáre sú viazané na anonymný identifikátor prehliadača (pozri F11).

## 2. Používateľský príbeh

> **Ako** budúci kupujúci nehnuteľnosti
> **chcem** zadať cenu nehnuteľnosti, akontáciu, úrokovú sadzbu a dobu splatnosti,
> **aby som** videl, koľko budem mesačne platiť, koľko ma úver bude stáť celkovo a ako by mimoriadne splátky skrátili jeho dobu – ešte predtým, než pôjdem do banky.

Doplnkové príbehy pre v2:

> **Ako** používateľ **chcem** uložiť si niekoľko variantov úveru pod vlastným názvom, **aby som** ich mohol neskôr porovnať.

> **Ako** používateľ **chcem** poslať odkaz na konkrétny variant partnerovi alebo poradcovi, **aby** videl rovnaké čísla bez toho, aby ich musel prepisovať.

### Akceptačné kritériá

1. **Ak** otvorím aplikáciu prvýkrát, **keď** sa stránka načíta, **potom** sa zobrazí kompletný výsledok pre predvolené hodnoty (cena 300 000, akontácia 60 000, sadzba 4,5 %, doba 30 rokov, daň 1 200/rok, poistenie 600/rok, mena EUR, prvá splátka budúci mesiac).
2. **Ak** zmením akýkoľvek vstup, **keď** píšem alebo posúvam posuvník, **potom** sa všetky výsledky, grafy a tabuľka aktualizujú bez tlačidla „Vypočítať“ (s oneskorením najviac ~300 ms na odpoveď API).
3. **Ak** sú vstupy platné, **potom** vidím celkovú mesačnú splátku a jej rozdelenie na istinu a úrok, mimoriadnu splátku a daň a poistenie.
4. **Ak** sú vstupy platné, **potom** vidím výšku úveru, celkové úroky, celkovú cenu úveru a dátum splatenia.
5. **Ak** zadám mimoriadnu mesačnú splátku väčšiu ako 0, **potom** vidím, o koľko skôr splatím úver a koľko ušetrím na úrokoch oproti stavu bez mimoriadnej splátky.
6. **Ak** zadám neplatnú hodnotu (napr. akontácia vyššia ako cena), **potom** vidím zrozumiteľnú chybovú hlášku a predchádzajúce výsledky sa zobrazia ako neaktuálne, nie prepočítané.
7. **Ak** zavriem a znova otvorím aplikáciu v tom istom prehliadači, **potom** sa obnovia moje posledné vstupy a zvolená téma.
8. **Ak** kliknem na *Stiahnuť CSV*, **potom** dostanem kompletný mesačný amortizačný harmonogram ako súbor.
9. **Ak** kliknem na *Uložiť scenár* a zadám názov, **potom** sa scenár objaví v zozname „Moje scenáre“ aj po obnovení stránky.
10. **Ak** pri uloženom scenári kliknem na *Zdieľať*, **potom** dostanem odkaz, ktorý po otvorení v inom prehliadači zobrazí rovnaké vstupy a výsledky len na čítanie.
11. **Ak** API nie je dostupné, **potom** vidím hlášku „Výpočet je dočasne nedostupný“ a posledné výsledky sú označené ako neaktuálne; aplikácia nespadne.

## 3. Funkcie

### F1 – Vstupy úveru (frontend)

| Vstup | Formát | Pravidlá |
| --- | --- | --- |
| Cena nehnuteľnosti | Suma, s posuvníkom (20 000 – 2 000 000) | Musí byť väčšia ako 0 |
| Akontácia | Suma **alebo** percento, navzájom synchronizované; posuvník 0 – 100 % | 0 alebo viac a menej ako cena |
| Úroková sadzba | Percento, s posuvníkom (0 – 15 %) | 0 – 50 % |
| Doba splatnosti | Predvoľby 10 / 15 / 20 / 25 / 30 rokov alebo vlastná hodnota | Celé roky, 1 – 50 |
| Prvá splátka | Mesiac a rok | Predvolene budúci mesiac |
| Mimoriadna mesačná splátka *(voliteľné)* | Suma, s posuvníkom (0 – 3 000) | 0 alebo viac |
| Daň z nehnuteľnosti / rok *(voliteľné)* | Suma | 0 alebo viac |
| Poistenie / rok *(voliteľné)* | Suma | 0 alebo viac |

- Číselné polia prijímajú formát `250,000.50` aj `250 000,50` bez ohľadu na jazyk prehliadača. Parsovanie robí frontend; do API idú už čísla.
- Po opustení poľa sa hodnota preformátuje s oddeľovačmi tisícov.
- *Obnoviť predvolené* vráti všetky vstupy na predvolené hodnoty.

### F2 – Validácia

- **Frontend** kontroluje vstupy pri každej zmene kvôli okamžitej odozve. Zobrazí sa prvá nájdená chyba v jednej hláške (oznámenej čítačkám obrazovky).
- **API** validuje znova a je autoritatívne. Neplatný vstup vráti `422` so zoznamom chýb (pole + kód + hláška). Frontend zobrazí prvú z nich.
- Kým je vstup neplatný, výsledky sú stlmené, neprepočítavajú sa a neplatný stav sa neukladá (ani do `localStorage`, ani do Supabase).

### F3 – Výpočet splátky (Python, balík `calc`)

- Mesačná splátka istiny a úroku podľa štandardného anuitného vzorca `P × r / (1 − (1 + r)^−n)`, kde `P` je výška úveru, `r` mesačná sadzba a `n` počet splátok. Pri sadzbe 0 % sa úver rozdelí rovnomerne na celú dobu.
- Každý mesiac sa úrok počíta zo zostatku; zvyšok splátky vrátane mimoriadnej splátky znižuje istinu.
- Peniaze sa počítajú v `Decimal`. Splátka aj mesačný úrok sa zaokrúhľujú na centy (ROUND_HALF_UP).
- Posledná splátka uhradí presne zvyšný zostatok. Rozdiel zo zaokrúhľovania sa tak premietne do poslednej splátky, nie do ďalšieho mesiaca.
- Daň a poistenie sa vydelia 12 a pripočítajú k mesačnej sume. Zostatok úveru neovplyvňujú.

### F4 – Súhrn výsledkov

- **Mesačná splátka:** celková mesačná suma s riadkom rozdelenia na istinu a úrok, mimoriadnu splátku a daň a poistenie.
- **Pruh rozdelenia splátky:** podiel istiny, úroku, mimoriadnej splátky a dane a poistenia v prvej splátke, s legendou.
- **Výška úveru:** s percentom akontácie a ukazovateľom LTV.
- **Celkové úroky:** s úrokmi ako percentom z úveru, alebo s ušetrenou sumou, ak je zadaná mimoriadna splátka.
- **Celková cena úveru:** istina plus úroky.
- **Dátum splatenia:** mesiac a rok poslednej splátky, trvanie a počet splátok.
- **Odznak „skôr“:** ak mimoriadna splátka skráti úver, ukáže o koľko (napr. „o 4 roky a 3 mesiace skôr“).

### F5 – Grafy (frontend)

- **Zostatok úveru:** zostatok v čase. Pri mimoriadnej splátke sa pre porovnanie zobrazí aj štandardný harmonogram.
- **Istina vs. úrok podľa rokov:** skladaný stĺpcový graf rozdelenia splátok v jednotlivých rokoch.
- Tooltipy ukazujú presné hodnoty pri prejdení myšou, pri fokuse z klávesnice a pri pohybe šípkami medzi bodmi.
- Grafy sa prekreslia pri zmene veľkosti okna alebo témy.

### F6 – Amortizačný harmonogram

- Tabuľka s prepínaním **ročného** a **mesačného** pohľadu: splátka, istina, úrok a zostatok za obdobie, s dátumami. Dáta pripraví API (`calc.schedule`).
- **Stiahnuť CSV:** export kompletného mesačného harmonogramu (číslo splátky, dátum, splátka, istina, úrok, zostatok). CSV generuje API. Názov súboru obsahuje menu, napr. `mortgage-schedule-eur.csv`.

### F7 – Mena a formátovanie

- Výber meny: EUR, USD, GBP, CZK, CHF, PLN. Zmena meny mení symboly, **nekonvertuje** hodnoty.
- Čísla, meny a dátumy sa formátujú podľa jazyka prehliadača (`Intl` na frontende). API vracia surové čísla ako reťazce s dvoma desatinnými miestami.

### F8 – Téma

- Svetlá a tmavá téma. Predvolene podľa systému, s ručným prepínačom; voľba sa zapamätá v `localStorage`.

### F9 – Lokálna perzistencia

- Posledné vstupy, mena a téma sa ukladajú do `localStorage` a obnovia sa pri ďalšej návšteve.
- V `localStorage` je aj anonymný `client_id` (UUID v4), vygenerovaný pri prvej návšteve.

### F10 – Prístupnosť a rozloženie

- Všetky ovládacie prvky majú popisy a dajú sa ovládať klávesnicou; predvoľby doby a prepínač harmonogramu sa správajú ako skupiny prepínačov (radio group).
- Grafy a tooltipy sú dosiahnuteľné a čitateľné z klávesnice.
- Rozloženie funguje na mobile, tablete aj desktope.

### F11 – Uložené scenáre (nové, Supabase)

- *Uložiť scenár* uloží aktuálne platné vstupy a menu pod názvom (1 – 100 znakov).
- Zoznam „Moje scenáre“ ukazuje scenáre patriace k `client_id` prehliadača, zoradené od najnovšieho, s mesačnou splátkou a dátumom poslednej úpravy.
- Scenár sa dá **načítať** (vstupy sa prepíšu), **premenovať**, **prepísať** aktuálnymi vstupmi a **zmazať** (s potvrdením).
- Limit 50 scenárov na `client_id`.
- Scenáre sú viazané na prehliadač. Po vymazaní dát prehliadača alebo na inom zariadení ich používateľ neuvidí (vedomé obmedzenie bez prihlásenia).

### F12 – Zdieľacie odkazy (nové, Supabase)

- *Zdieľať* pri scenári vygeneruje odkaz v tvare `/s/{slug}`, kde `slug` je náhodný 10-znakový reťazec (base62).
- Otvorenie odkazu zobrazí vstupy a výsledky **len na čítanie** s tlačidlom *Otvoriť v kalkulačke*, ktoré skopíruje vstupy do vlastnej kalkulačky.
- Vlastník môže zdieľanie **zrušiť**; odkaz potom vráti stránku „Odkaz už neplatí“ (HTTP `404`).
- Zdieľaný scenár nezobrazuje `client_id` ani iné identifikátory vlastníka.

### F13 – Log výpočtov (nové, Supabase)

- API zapíše každý úspešný výpočet do tabuľky `calculation_log`: vstupy, kľúčové výsledky, zdroj (`live`, `scenario`, `share`) a trvanie výpočtu v ms.
- Log **neobsahuje** `client_id`, IP adresu ani iné osobné údaje.
- Pri živom písaní sa loguje najviac jeden výpočet za 5 sekúnd na reláciu prehliadača (frontend posiela hlavičku `X-Log: 0` pre medzivýpočty).
- Zlyhanie zápisu do logu nesmie zlyhať výpočet.
- Záznamy staršie ako 90 dní sa mažú.

## 4. Mimo rozsahu

- Poplatky, poistenie úveru (PMI), náklady na uzavretie a premenlivé úrokové sadzby.
- Konverzia mien.
- Používateľské účty a prihlásenie (scenáre sú anonymné, viazané na prehliadač).
- Úprava zdieľaného scenára cez zdieľací odkaz.
- Výsledky sú odhady; čísla banky sa môžu líšiť kvôli poplatkom, zaokrúhľovaniu a zmenám sadzieb.
