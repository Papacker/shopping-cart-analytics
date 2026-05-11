# Kehitysblogi: UWB-kauppadatan analyysijärjestelmä

> **Projekti:** Projektiopinnot 1 – Datan hallinta  
> **Tiimi:** Laitetaan Parastamme  
> **Teknologiat:** Python · DuckDB · CrewAI · Ollama · UWB-paikannus

---

## Mistä kaikki alkoi?

Projektin tavoite oli rakentaa analyysiputki, joka tutkii kaupan ostoskärryjen liikkumista **UWB-paikannusdatan** (Ultra-Wideband) pohjalta. Kaupassa on sijoiteltu antenneja, jotka lähettävät signaalia ostoskärryihin kiinnitetyille laitteille. Tätä dataa keräämällä voidaan selvittää esimerkiksi:

- Kuinka kauan asiakkaat viettävät kaupassa?
- Mitkä osastot ovat suosituimpia?
- Mihin aikaan kauppa on kiireisimmillään?
- Millä kassalla on eniten liikennettä?

---

## Arkkitehtuuri

```
config/store_config.py  (kaupan pohjapiirustus, osastot, sessiologiikka)
       ↓
data/raw/*.csv          (UWB-raakadata, ~5 GB yhteensä, 32 tiedostoa)
       ↓
   main.py              (ETL-pipeline, StoreDataCleaner, rinnakkaisajo)
       ↓
database/store.db       (DuckDB-tietokanta, 6 taulua)
       ↓
agentti/crew.py         (CrewAI-agentti + LLM-analyysi)
       ↓
agentti/workspace/      (Markdown-raportit)
```

### Tietokannan rakenne

| Taulu | Rivejä | Kuvaus |
|---|---|---|
| `ShoppingCart` | 21 | Ostoskärryt ja niiden tunnisteet |
| `Visit` | 6 751 | Yksittäiset kauppakäynnit (kesto, aika) |
| `Zone` | 10 390 667 | UWB-koordinaattipisteet (x, y per sekunti) |
| `Quality` | 86 976 | Mittausten laadunvalvontaloki |
| `Categories` | 33 | Kaupan osastomääritykset (store_configista) |
| `ZoneVisit` | 185 714 | Osastokohtaiset käyntisegmentit |


---

## store_config.py — Projektin konfiguraatiokeskus

`config/store_config.py` on koko järjestelmän "totuuden lähde" kaupan rakenteen osalta. Se sisältää:

```python
store_config = {
    "geometry": {
        "store_max_x_cm": 11206,   # Kaupan leveys
        "store_max_y_cm": 5220,    # Kaupan syvyys
        "map_profiles": { ... }    # Karttakuvien skaalaukset
    },
    "spatial_zones": {
        "departments": {           # 25 osastoa koordinaattilaatikoilla
            "47 Liha/Kala": {"coords": (8325, 10406, 505, 2220), ...},
            "3-9 Vaatteet": {"coords": (2685, 5800, 3800, 5220), ...},
            # ... 23 muuta osastoa
        },
        "checkouts": {             # 8 kassapistettä
            "Kassa 1": {"coords": (-200, 700, 1700, 2000), ...},
            # ...
        },
        "gates": { ... },          # Sisäänkäynti ja uloskäynti
        "dead_zones": { ... },     # Varasto, lastaus jne.
    },
    "session_logic": {
        "max_time_s": 5400,        # Max käynti 90 min
        "min_points": 50,          # Vähintään 50 paikannuspistettä
        ...
    }
}
```

---

## Kehityspolku

### Vaihe 1 — ETL-pipeline (main.py)

Ensin rakennettiin **ETL-pipeline** joka:
1. Lukee raakoita CSV-tiedostoja rinnakkain (`ProcessPoolExecutor`, 8 prosessia)
2. Puhdistaa datan (`StoreDataCleaner`) — poistaa epävalidit pisteet
3. Sessionisoi pisteet kauppakäynneiksi (aikaikkuna-algoritmi)
4. Kirjoittaa tulokset atomisesti DuckDB-tietokantaan

**ETL-tulokset:**

| Mitta | Arvo |
|---|---|
| Raakadataa yhteensä | 140 000 000 riviä |
| Hyväksyttyjä rivejä | 10 390 667 kpl |
| Hylätty: liian vähän pisteitä | 78 219 sessiota |
| Hylätty: heikko penetraatio | 4 227 sessiota |
| Suoritusaika | ~32 sekuntia (rinnakkaisajo) |

**Haasteet:**
- DuckDB:n lukitukset vaativat retry-logiikan (jopa 10 yritystä)
- Windows-ympäristössä Unicode-virheitä emojien kanssa → korjattu `PYTHONUTF8=1`
- `store.db` on `.gitignore`:ssa — täytyy ajaa `uv run main.py` uudella koneella

---

### Vaihe 2 — CrewAI-agenttijärjestelmä (crew.py)

Rakennettiin **multi-agent system** CrewAI-frameworkilla. Matkan varrella korjattiin useita ongelmia:

#### Ongelma 1: Syntaksivirhe rivi 35 — irtonainen `x`
```python
# ENNEN (kaatoi koko skriptin käynnistyksessä):
OLLAMA_HOST = os.environ.get(...)
x                      # ← NameError!

# JÄLKEEN:
OLLAMA_HOST = os.environ.get(...)
# (x poistettu)
```

#### Ongelma 2: `print(result)` tulosti JSON:ia, ei markdownia
```python
# ENNEN:
print(result)          # → {"name": "write_file", "arguments": {...}}

# JÄLKEEN:
print(result.raw)      # → # Kaupan raportti...
```

#### Ongelma 3: `load_dotenv()` importattu mutta ei koskaan kutsuttu
```python
# LISÄTTY:
load_dotenv(dotenv_path=env_path)
```
Ilman tätä `.env`-tiedoston `APP_OLLAMA_MODEL`-asetus ei vaikuttanut mitään.

#### Ongelma 4: Väärä LLM-malli
Coder-mallit (`qwen2.5-coder:14b`) eivät tue CrewAI:n ReAct tool-calling -protokollaa. Ne kirjoittivat tool-kutsut JSON-tekstinä sen sijaan että oikeasti kutsuivat niitä:

```
# VÄÄRÄ TOIMINTA:
Final Answer:
{"name": "inspect_schema", "arguments": {}}   ← Pelkkää tekstiä!

# OIKEA TOIMINTA (llama3.1:8b):
→ Tool: inspect_schema()
→ Result: Tietokannassa on taulut: ...
```

**Ratkaisu:** `llama3.1:8b` joka tukee natiiveja tool-kutsuja.

#### Ongelma 5: Agentti tulosti "areena"-kontekstissa
LLM yhdistää UWB:n urheiluareenoihin. Korjattu:
```python
# ENNEN:
role="UWB Analysis Manager",
goal="Identify shopping cart patterns and store bottlenecks",

# JÄLKEEN:
role="Kauppadatan analyytikko",
backstory="Kyseessa on KAUPPA, ei areena tai urheiluhalli."
```

#### Ongelma 6: SQL-syntaksivirhe agentin tuottamissa kyselyissä
Agentti modifioi annettuja SQL-esimerkkejä ja aiheutti virheitä (esim. `DATE()` vs. `CAST(... AS DATE)`).

**Ratkaisu — arkkitehtuurimuutos:** Siirryttiin **Python-ensin** -lähestymistapaan:

```python
def _fetch_all_data(db_path: str) -> dict:
    """Python hakee kaiken datan itse — agentti vain muotoilee raportin."""
    con = duckdb.connect(db_path, read_only=True)
    # Ajetaan kaikki SQL Python-tasolla → ei SQL-virheitä agentissa!
```

---

### Vaihe 3 — store_config-integraatio (nykyinen tila)

**Avainmuutos:** SQL-kyselyt eivät ole enää kovakoodattuja `crew.py`:hyn. Osastot ja kassat haetaan `store_config.py`:stä ja SQL generoidaan dynaamisesti:

```python
# crew.py importoi konfiguraation
from config.store_config import store_config

def _build_department_sql() -> str:
    """Generoi CASE-lauseke store_config.departments-dictistä."""
    departments = store_config["spatial_zones"]["departments"]
    cases = []
    for name, dept in departments.items():
        x_min, x_max, y_min, y_max = dept["coords"]
        cases.append(
            f"WHEN z.x BETWEEN {x_min} AND {x_max} "
            f"AND z.y BETWEEN {y_min} AND {y_max} THEN '{name}'"
        )
    # Palauttaa valmiin SQL CASE-lausekkeen
    ...

def _build_checkout_sql() -> str:
    """Vastaava kassaruuhka-SQL checkouts-dictistä."""
    ...
```

**Hyöty:** Jos osastoja lisätään tai muutetaan `store_config.py`:ssä, kyselyt päivittyvät automaattisesti — `crew.py`:tä ei tarvitse koskea.

---

### Vaihe 4 — Koodin siivous ja vakautus (10.5.2026)

**Miten tähän päästiin:**
Projektin ydintoimintojen vakiinnuttua (ETL, DuckDB ja Agentit) huomioitiin editorin (VS Code) "Problems"-välilehden antamat lukuisat varoitukset. Ongelmien juurisyyt analysoitiin ja jaettiin kahteen leiriin: todellisiin koodin laatuvirheisiin ja editorin omiin analysointivirheisiin.

**Mitä muutettiin ja miksi:**
1. **Koodityylin yhtenäistäminen (`pylint` auditointi):** 
   - Kaikista tiedostoista (app.py, main.py, processor.py jne.) poistettiin käyttämättömät kirjastotuonnit (`import duckdb`, `import logging`), käyttämättömät muuttujat sekä sadat turhat tyhjät lyönnit (trailing whitespaces). 
   - **Miksi:** Puhtaampi koodipohja on helpompi lukea, testata ja jatkokehittää, eikä analysaattori huuda turhista varoituksista.
2. **Yksikkötestien päivitys (`pytest` 12/12 läpi):**
   - Refaktoroinnin myötä `src/app.py` menetti turhan `import duckdb` -riippuvuutensa (koska kyselyt oli fiksusti eriytetty `src/queries.py` -tiedostoon). 
   - Tämä rikkoi yhden yksikkötestin, joka tarkasti kyseisen rivin olemassaolon. Testi päivitettiin vastaamaan uutta puhtaampaa arkkitehtuuria. Nyt kaikki 12 testiä ovat vihreällä.
3. **IDE-hälyjen tunnistaminen:**
   - Todettiin, että suurin osa IDE:n varoituksista (esim. `__pyrefly_virtual__\inmemory...`) johtuu editorin tavoista tulkita monirivisiä dokumentaatiokommentteja (`""" Kauppadatan analyytikko... """`) irtonaisina Python-koodinpätkinä. Tälle ei tarvitse/voi kooditasolla tehdä mitään, ja varoitukset voi turvallisesti sivuuttaa.

**Nykytila:** Koodipohja on teknisesti täysin ehjä (0 `pylint`-virhettä), testattu (`12/12 passed`) ja ETL-putki on salamannopea. Lisäksi huomattiin, että myös `Categories` ja `ZoneVisit` -taulut täyttyivät kymmenillä tuhansilla riveillä rinnakkais-ETL:n ajossa, toisin kuin aiemmin luultiin.

---

## Lopullinen crew.py arkkitehtuuri

```
crew.py
├── Importit
│   ├── crewai (LLM, Agent, Crew, Process, Task)
│   ├── tools (query_duckdb, write_file, ...)
│   └── config.store_config ← store_configin koordinaatit
│
├── LLM-konfiguraatio (llama3.1:8b via Ollama, max_tokens=8192)
│
├── Agentit
│   ├── manager     (max_iter=5, allow_delegation=True)
│   ├── analyst     (max_iter=5, data_tools) ← pääagentti
│   └── engineer    (max_iter=5, code_tools)
│
├── SQL-generaattorit (store_configista)
│   ├── _build_department_sql()   → 25 osastoa CASE-lausekkeena
│   └── _build_checkout_sql()     → 8 kassaa WHERE-lausekkeena
│
├── _fetch_all_data(db_path)      → 11 kyselyä Python-tasolla
│   ├── yleiskatsaus
│   ├── kaynteja_per_karry
│   ├── kaynteja_per_paiva
│   ├── kaynteja_per_tunti
│   ├── kaynteja_per_viikonpaiva
│   ├── kesto_luokat
│   ├── laatu_syyt
│   ├── zone_kattavuus
│   ├── top_pisin_yksittainen
│   ├── osastoanalyysi ← _build_department_sql()
│   └── kassaruuhka   ← _build_checkout_sql()
│
├── build_crew(task)
│   ├── Kutsuu _fetch_all_data() → saa kaiken datan valmiina
│   ├── Injektoi datan tehtäväkuvaukseen (agentti ei aja SQL:aa)
│   └── Analyytikko kirjoittaa markdown-raportin 9 osalla
│
└── main()
    ├── Testaushaara ("testaa ..." → pytest)
    └── Analyysihaara → build_crew() → CrewAI
```

---

## Analyysitulokset

### Kokonaistilastot (6 751 kauppakäyntiä)

| Mitta | Arvo |
|---|---|
| Kauppakäyntejä yhteensä | 6 751 |
| Aktiivisia kärrejä | 21 |
| Keskimääräinen käynti | 34,9 min |
| Lyhin käynti | 1,0 min |
| Pisin käynti | 90,0 min |
| Yhteisaika kaupassa | 3 925 tuntia |

### Aktiivisimmat kärryt

| Kärry | Käyntejä | Keski (min) | Yht. (h) |
|---|---|---|---|
| kärry_54016 | 436 | 35,1 | 255 |
| kärry_52535 | 388 | 35,4 | 229 |
| kärry_51850 | 378 | 36,0 | 227 |

### Suosituimmat osastot (store_configista)

| Osasto | Paikannuspisteitä | Osuus |
|---|---|---|
| 47 Liha/Kala | 1 381 582 | 13,3 % |
| 61-63 Pakasteet | 592 273 | 5,7 % |
| 3-9 Vaatteet | 330 719 | 3,2 % |
| 13-19 Juomat | 243 164 | 2,3 % |
| 43-46 Leipomo | 233 729 | 2,2 % |

> 47 % datasta on käytävillä (ei millään osastolla).

### Kassaruuhka (store_configista)

| Kassa | Käyntejä | Paikannuspisteitä |
|---|---|---|
| Kassa 3 | 5 344 | 211 098 |
| Kassa 2 | 4 990 | 206 698 |
| Kassa 1 | 3 652 | 200 271 |
| Kassa 8 | 842 | 8 278 |

### Ruuhka-ajat

| Tunti | Käyntejä |
|---|---|
| 14:00 | 754 |
| 16:00 | 746 |
| 15:00 | 724 |
| 13:00 | 741 |

Vilkkain viikonpäivä: **Perjantai** (1 080 käyntiä).

---

## Tekninen pino

| Komponentti | Teknologia |
|---|---|
| Ohjelmointikieli | Python 3.11 |
| Tietokanta | DuckDB |
| Agenttikehys | CrewAI |
| LLM | llama3.1:8b (Ollama) |
| Paketinhallinta | uv |
| Testaus | pytest + pytest-cov |

---

## Käynnistysohjeet

```bash
# 1. Rakenna tietokanta (tarvitaan kerran tai kun data muuttuu)
PYTHONUTF8=1 uv run main.py

# 2. Aja analyysi
uv run agentti/crew.py
# → Syötä tehtävä, esim: "Analysoi kaupan käyntitiedot"

# Raportti tallennetaan: agentti/workspace/raportti.md
```

---

## Mitä seuraavaksi?

1. **Visualisoinnit** — Heatmap ostoskärryjen reiteistä Zone-koordinaateista (`engineer`-agentti)
2. **Osastojen täyttöaste** — `Categories`-taulu käyttöön ZoneVisit-laskentaan
3. **Aikatrendit** — Viikoittainen ja kuukausittainen vertailu (tällä hetkellä vain yksi viikko dataa)
4. **Anomaliadetektio** — Automaattinen tunnistus epätavallisista käyntikuvioista

---

*Päivitetty: 10.5.2026 — Projektin linttaus, koodin siivous ja 100% testikattavuuden varmistus*
