# 🛒 UWB-Myymäläanalytiikka — Laitetaan parastamme

Tämä projekti analysoi myymälän asiakasliikennettä **UWB-paikannusdatan** (Ultra-Wideband) avulla.  
Ostoskärryihin kiinnitetyt UWB-laitteet lähettävät sijaintitietoa, jonka pohjalta voidaan tutkia  
esimerkiksi: *missä osastoilla kärry viipyy, kuinka kauan yksi ostoskerta kestää ja mitkä alueet ovat ruuhkaisimpia.*

Projekti koostuu kolmesta pääosasta:

| Osa | Kuvaus |
|---|---|
| **ETL-putki** (`main.py`) | Lukee CSV-tiedostot, puhdistaa datan ja tallentaa sen tietokantaan sekä parquet muodossa data/processed kansioon. |
| **Streamlit-dashboard** (`src/app.py`) | Interaktiivinen selainpohjainen analysointinäkymä. |
| **AI-agentti** (`agentti/crew.py`) | Tekoälyagentti, jonka avulla käyttäjä voi kysellä haluamiaan tietoja tietokannasta ja saada vastaukseksi selkeän raportin suomeksi. |

---

## 📋 Vaatimukset

Varmista ennen asennusta, että koneellasi on seuraavat ohjelmat:

| Ohjelma | Versio | Käyttötarkoitus |
|---|---|---|
| **Visual Studio Code** | ≥ 1.119 | Koodieditori |
| **Python** | ≥ 3.11 | Ohjelmointikieli |
| **uv** | ≥ 0.11.12 | Python-pakettien hallinta |
| **Ollama** | ≥ 0.23.1 | AI-mallin ajaminen paikallisesti |

### Ohjelmien asennus

```bash
# 1. uv (Python-paketinhallinta)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Ollama (Ajaa kielimalleja paikallisesti)
curl -fsSL https://ollama.com/install.sh | sh

# 3. Ladataan AI-malli (~9 GB) — tarvitaan vain agentin käyttöön
ollama pull qwen2.5-coder:14b
```

> **Huom:** Ollama ja AI-malli tarvitaan **vain**, jos haluat käyttää AI-agenttia (`agentti/crew.py`).  
> Streamlit-dashboard ja ETL-putki toimivat ilman Ollamaa.

---

## ⚙️ Projektin asennus

```bash
# 1. Kloonaa repositorio
git clone git@gitlab.dclabra.fi:ttm25sai/projekti1/projektiopinnot-1-datan-hallinta-laitetaan-parastamme.git
cd projektiopinnot-1-datan-hallinta-laitetaan-parastamme

# 2. Asenna Python-riippuvuudet
uv sync
```

### Raakadatan sijoittaminen

Kopioi UWB-laitteiden tuottamat CSV-tiedostot hakemistoon:

```
data/raw/
```

ETL-putki käsittelee automaattisesti kaikki sieltä löytämänsä tiedostot.

---

## 🔐 Ympäristömuuttujat

Luo projektin **juurikansioon** tiedosto nimeltä `.env` ja lisää siihen seuraavat rivit.  
*(Tiedostoa ei tallenneta Gitiin.)*

```dotenv
# Ollama-asetukset (tarvitaan vain AI-agentin käyttöön)
OLLAMA_HOST=http://127.0.0.1:11434
APP_OLLAMA_MODEL=qwen2.5-coder:14b
```

| Muuttuja | Oletusarvo | Selitys |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollamapalvelimen osoite |
| `APP_OLLAMA_MODEL` | `qwen2.5-coder:14b` | Käytettävä kielimalli |

---

## 🚀 Käyttö

### 1. Streamlit-dashboard (suositeltava tapa aloittaa)

```bash
uv run streamlit run src/app.py
```

Avaa selaimessa: **http://localhost:8501**

Dashboardissa on kuusi välilehteä:

| Välilehti | Sisältö |
|---|---|
| 🏥 **Datan laatu** | Näyttää hylättyjen rivien syyt ja tilastot |
| 🚶 **Liikennevirrat** | Käyntimäärät ajan suhteen |
| 🏪 **Osastoanalyysi** | Ostoskärryjen viipymä eri osastoilla |
| 🛒 **Kärrydynamiikka** | Yksittäisten kärryjen käyttäytyminen |
| 🔥 **Heatmap** | Lämpökartta kärryjen liikkeistä pohjakuvalla |
| 🧠 **Advanced insights** | Edistyneet analyysit |

**ETL-putken ajaminen dashboardista:**  
Sivupalkissa on nappi **"🚀 Aja ETL-putki"** — paina sitä ensimmäisellä käyttökerralla tai kun lisäät uusia CSV-tiedostoja.

---

### 2. ETL-putki komentoriviltä

Jos haluat ajaa datan käsittelyn suoraan terminaalista:

```bash
uv run python main.py
```

ETL-putki:
1. Lukee `data/raw/` -kansion CSV-tiedostot
2. Puhdistaa datan
3. Tallentaa tulokset `database/store.db` -tietokantaan
4. Tallentaa kopiot `data/processed/` -kansioon (Parquet-muoto)

---

### 3. AI-agentti

AI-agentti analysoi tietokantadataa ja kirjoittaa raportin suomeksi.

```bash
# Käynnistä Ollama taustalle
ollama serve &

# Käynnistä agentti
uv run python agentti/crew.py
```

Seuraavaksi agentti kysyy "Mitä tiimin pitäisi tehdä?"

```
Mitä tiimin pitäisi tehdä? > Analysoi kärrydataa ja tee raportti
```

Vastaus tulostuu terminaaliin ja raportti tallentuu myös tiedostoon: `agentti/workspace/raportti.md`

### 4. Testien ajaminen

```bash
# Aja testit kaikille tiedostoille
uv run pytest tests/ -v

# Voit ajaa myös testejä erikseen
uv run pytest tests/test_main.py -v

uv run pytest tests/test_app.py -v

uv run pytest tests/test_crew.py -v
```

---

### 5. Yksittäiset Jupyter-notebookit

Notebookit sisältävät yksityiskohtaisia analyysejä ja kokeiluja:

```bash
uv run jupyter lab
```

| Notebook | Sisältö |
|---|---|
| `raakadata.ipynb` | Datan ensikatsaus |
| `datan_puhdistus.ipynb` | Puhdistuslogiikan kehitys |
| `etl_puhdistus.ipynb` | ETL-prosessin testaus |
| `duckdb_asiointianalyysi.ipynb` | SQL-kyselyt DuckDB:llä |
| `kassojen_kayttoaste.ipynb` | Kassalinjojen käyttöasteanalyysi |
| `liikkuminen_heatmap.ipynb` | Lämpökartat kärryjen liikkeistä |
| `poistettu_data.ipynb` | Hylätyn datan tutkiminen |

---

## 🧰 Teknologiapino

| Teknologia | Versio | Rooli |
|---|---|---|
| **Python** | ≥ 3.11 | Ohjelmointikieli |
| **DuckDB** | ≥ 1.5 | SQL-tietokanta |
| **Streamlit** | ≥ 1.56 | Interaktiivinen web-dashboard |
| **Pandas** | ≥ 3.0 | Datan käsittely |
| **NumPy** | ≥ 2.4 | Numeerinen laskenta |
| **Matplotlib** | ≥ 3.10 | Kaavioiden piirto |
| **Seaborn** | ≥ 0.13 | Tilastokaaviot |
| **Plotly** | ≥ 6.6 | Interaktiiviset kaaviot |
| **SciPy** | ≥ 1.17 | Tieteellinen laskenta (heatmap-suodatus) |
| **CrewAI** | ≥ 1.12 | AI-agenttikehys |
| **Ollama** | ≥ 0.23.1 | Paikallinen LLM-palvelin |
| **uv** | ≥ 0.11.12 | Python-paketinhallinta |

### Hakemistorakenne

```
.
├── main.py                  # ETL-putken pääohjelma
├── src/
│   ├── app.py               # Streamlit-sovellus
│   ├── charts.py            # Kaavioiden piirtologiikka
│   ├── processor.py         # Datan puhdistusluokka (StoreDataCleaner)
│   ├── queries.py           # SQL-kyselyt
│   ├── style.css            # Dashboardin ulkoasu
│   └── tabs/                # Dashboard-välilehdet (tab1–tab6)
├── agentti/
│   ├── crew.py              # AI-agenttien kokoonpano ja käynnistys
│   ├── tools/               # Agentin työkalut (SQL, tiedostot, Python)
│   └── workspace/           # Agentin tallentamat raportit
├── database/
│   ├── schema_duckdb.sql    # Tietokantaskeema
│   └── store.db             # DuckDB-tietokanta (ei Gitissä)
├── config/
│   └── store_config.py      # Myymälän pohjakartta ja osastorajat
├── data/
│   ├── raw/                 # Alkuperäiset CSV-tiedostot (ei Gitissä)
│   └── processed/           # ETL:n tuottamat Parquet-tiedostot (ei Gitissä)
├── notebooks/               # Jupyter-notebookit
├── tests/                   # Automaattiset testit
└── pyproject.toml           # Projektin riippuvuudet
```

---

## 📄 Tekijät

**Suvi Niemi, Teo Juurinen, Mikko Valkealahti, Juhani Rautio**

