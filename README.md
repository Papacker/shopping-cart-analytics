# UWB-Myymäläanalytiikka — Laitetaan parastamme

Tämä projekti analysoi myymälän asiakasliikennettä **UWB-paikannusdatan** (Ultra-Wideband) avulla.  
Ostoskärryihin kiinnitetyt UWB-laitteet lähettävät sijaintitietoa, jonka pohjalta voidaan tutkia  
esimerkiksi: *missä osastoilla kärry viipyy, kuinka kauan yksi ostoskerta kestää ja mitkä alueet ovat ruuhkaisimpia.*

Projekti koostuu neljästä pääosasta:

| Osa | Kuvaus |
|---|---|
| **ETL-putki** (`main.py`) | Lukee CSV-tiedostot, puhdistaa datan ja tallentaa sen tietokantaan sekä parquet-muodossa **data/processed**-kansioon. |
| **Streamlit-dashboard** (`src/app.py`) | Selainpohjainen analysointinäkymä (7 välilehteä). |
| **FastAPI-backend** (`src/backend.py`) | REST-rajapinta agentin ohjaukseen, heatmapin generointiin ja raporttien luontiin. |
| **AI-agentti** (`agentti/crew.py`) | Tekoälyagentti jonka kielimallin voi valita useammasta vaihtoehdosta. Tämän avulla käyttäjä voi kysellä tietoja tietokannasta ja saada vastaukseksi selkeän raportin suomeksi. Agentti muistaa jo käydyn keskustelun. |

---

## Vaatimukset

Varmista ennen käyttöä, että koneellasi on seuraavat ohjelmat, koodieditoreista voit valita kumman itse haluat, et siis tarvitse molempia.

| Ohjelma | Versio | Käyttötarkoitus |
|---|---|---|
| **Visual Studio Code** | ≥ 1.119 | Koodieditori |
| **Antigravity IDE** | 1.23.2 | Koodieditori |
| **Python** | ≥ 3.11 | Ohjelmointikieli |
| **uv** | ≥ 0.11.12 | Python-pakettien hallinta |
| **Ollama** | ≥ 0.23.1 | AI-mallin ajaminen paikallisesti |

### Ohjelmien asennus

**Huom:** Ollama ja AI-malli tarvitaan **vain**, jos haluat käyttää AI-agenttia.  
Streamlit-käyttöliittymä ja ETL-putki toimivat ilman Ollamaa.

**Aja terminaalissa seuraavat komennot:**
```bash
# 1. uv (Python-paketinhallinta)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Asenna ja ota käyttöön oikea Python-versio uv:n avulla
uv python install 3.11

# 3. Ollama (Ajaa kielimalleja paikallisesti)
curl -fsSL https://ollama.com/install.sh | sh

# 4. Ladataan käytettävä AI-malli — tarvitaan vain mikäli käytät agenttia.
# Voit aloittaa kokeilun lataamalla esimerkiksi jonkun seuraavista vaihtoehdoista alla olevilla komennoilla.
ollama pull qwen3.6:35b-a3b     # ~22 GB, suositus — paras yleisanalyysiin
ollama pull llama3.1:8b         # ~5 GB, tasapainoinen vaihtoehto
ollama pull qwen2.5-coder:14b   # ~9 GB, koodianalyysiin erikoistunut
ollama pull qwen2.5-coder:7b    # ~4 GB, kevyempi koodivaihtoehto
```

---

## Projektin asennus

```bash
# 1. Kloonaa repositorio
git clone git@gitlab.dclabra.fi:ttm25sai/projekti1/projektiopinnot-1-datan-hallinta-laitetaan-parastamme.git
cd projektiopinnot-1-datan-hallinta-laitetaan-parastamme

# 2. Asenna Python-riippuvuudet
uv sync
```

### Raakadatan lisääminen

Kopioi UWB-laitteiden tuottamat CSV-tiedostot hakemistoon:

```
data/raw/
```

ETL-putki käsittelee automaattisesti kaikki sieltä löytämänsä tiedostot.

---

## Ympäristömuuttujat

Luo projektin **juurikansioon** tiedosto nimeltä **.env**, voit kopioida tiedostoon seuraavan oletusarvoisen sisällön:

```
# Ollama-palvelimen paikallinen oletusarvoinen osoite
OLLAMA_HOST=http://127.0.0.1:11434
APP_OLLAMA_MODEL=qwen3.6:35b-a3b

# Oletuskielimalli on qwen3.6:35b-a3b (käytetään komentoriviltä agenttitiimille keskusteltaessa)
# Käyttöliittymää käytettäessä se hakee mallit automaattisesti Ollama-palvelimelta ja näyttää ne listana.

# Esimerkkivaihtoehtoja (Muista asentaa ensin terminaalin kautta: ollama pull <malli>):
#   qwen3.6:35b-a3b
#   llama3.1:8b
#   qwen2.5-coder:14b
#   qwen2.5-coder:7b
```

**.env**-tiedosto ei tallennu Gitiin.


| Muuttuja | Oletusarvo | Selitys |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama-palvelimen osoite |
| `APP_OLLAMA_MODEL` | `qwen3.6:35b-a3b` | Oletuskielimalli **komentorivikäytölle** |

---

## Käyttö

### 1. launcher.py tiedosto — suositeltava tapa käynnistää koko projekti

**Aja terminaalissa komento:**
```bash
uv run scripts/launcher.py
```

Tämä käynnistää automaattisesti:
- **FastAPI-backendin** portissa `8000`
- **Streamlit-frontendin** portissa `8501`

Avaa selaimessa: **http://localhost:8501**  

Sivustolla sinulla on käytettävissä seitsemän välilehteä.

| Välilehti | Sisältö |
|---|---|
| **Datan laatu** | Näyttää hylättyjen rivien syyt ja tilastot |
| **Liikennevirrat** | Käyntimäärät ajan suhteen |
| **Osastoanalyysi** | Ostoskärryjen viipymä eri osastoilla |
| **Kärrydynamiikka** | Yksittäisten kärryjen käyttäytyminen |
| **Lämpökartat** | Lämpökartta kärryjen liikkeistä pohjakuvalla |
| **Syvälliset havainnot** | Syvällisemmät analyysit |
| **Asiakkaalle** | Tekoälyagentin chat-näkymä ja raporttien generointi |

**ETL-putken ajaminen dashboardista:**  
Sivupalkissa on nappi **"🚀 Aja ETL-putki"** — paina sitä ensimmäisellä käyttökerralla tai kun lisäät uusia CSV-tiedostoja.

**Kielimallin valinta:**  
Sivupalkissa voit valita, mitä Ollama-mallia agentti käyttää. Dashboard hakee automaattisesti saatavilla olevat mallit Ollama-palvelimelta ja listaa ne valikkoon.

Kun haluat lopettaa sovelluksen käyttämisen, paina terminaalissa **Ctrl+C**

---

### 2. Streamlit-dashboardin manuaalinen käynnistys

**Aja terminaalissa komento:**
```bash
uv run streamlit run src/app.py
```

Avaa selaimessa osoite: **http://localhost:8501**

Lopetus terminaalissa **Ctrl+C**

---

### 3. ETL-putken käyttäminen komentoriviltä

Jos haluat ajaa datan käsittelyn suoraan terminaalista, kirjoita komento:
```bash
uv run python main.py
```

ETL-putki:
1. Lukee `data/raw/` -kansion CSV-tiedostot
2. Puhdistaa datan
3. Tallentaa tulokset `database/store.db` -tietokantaan
4. Tallentaa kopiot `data/processed/` -kansioon (Parquet-muoto)

---

### 4. AI-agentti

AI-agenttitiimi analysoi tietokantadataa ja kirjoittaa raportin suomeksi.  
Agenttitiimissä on viisi erikoistunutta roolia:

| Rooli | Tehtävä |
|---|---|
| **Kauppa-analyysin johtaja** | Koordinoi tiimiä ja raportoi tulokset suomeksi|
| **Kauppadatan analyytikko** | SQL-analyysit ja markdown-raporttien kirjoittaminen |
| **Python-visualisoija** | Kaaviot ja heatmapit Python-koodilla |
| **Ali Baba** | Laskenta ja visualisoinnit, tuloksien tallentaminen erilliseen kansioon |
| **Kaupan liiketoiminnan kehittäjä** | Liiketoiminnan konsultointi ja internet-haku |

**Agentilla on keskustelumuisti** — se muistaa aiemmat kysymykset ja pyrkii vastaamaan jatkokysymyksiin aiemman keskustelun huomioiden.

#### AI-agentin käyttäminen komentoriviltä

```bash
# Käynnistä Ollama taustalle
ollama serve &

# Käynnistä agentti
uv run python agentti/crew.py
```

Seuraavaksi agentti kysyy tehtävää:

```
Mita tiimin pitaisi tehda?
```

Kirjoita haluamasi kysymys, vastaus tulostuu terminaaliin ja raportti tallentuu tiedostoon: `agentti/workspace/raportti.md`

---

### 5. Testien ajaminen komentoriviltä

```bash
# Aja testit kaikille tiedostoille
uv run pytest tests/ -v

# Voit ajaa myös testejä erikseen
uv run pytest tests/test_main.py -v

uv run pytest tests/test_app.py -v

uv run pytest tests/test_crew.py -v
```

---

### 6. Yksittäiset Jupyter-notebookit

Notebookit sisältävät yksityiskohtaisia analyysejä ja kokeiluja:

```bash
uv run jupyter lab
```

Avaa selaimessa osoite: http://localhost:8888

Lopetus terminaalissa **Ctrl+C**

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

## Teknologiat

| Teknologia | Versio | Rooli |
|---|---|---|
| **Python** | ≥ 3.11 | Ohjelmointikieli |
| **DuckDB** | ≥ 1.5 | SQL-tietokanta |
| **Streamlit** | ≥ 1.56 | Interaktiivinen web-dashboard |
| **FastAPI** | ≥ 0.136 | REST-backend AI-agentin käyttöön |
| **Uvicorn** | ≥ 0.42 | ASGI-palvelin FastAPI:lle |
| **Pandas** | ≥ 3.0 | Datan käsittely |
| **NumPy** | ≥ 2.4 | Numeerinen laskenta |
| **Matplotlib** | ≥ 3.10 | Kaavioiden piirto |
| **Seaborn** | ≥ 0.13 | Tilastokaaviot |
| **Plotly** | ≥ 6.6 | Interaktiiviset kaaviot |
| **SciPy** | ≥ 1.17 | Tieteellinen laskenta (heatmap-suodatus) |
| **CrewAI** | ≥ 1.12 | AI-agenttikehys |
| **Ollama** | ≥ 0.23.1 | Paikallinen LLM-palvelin |
| **DuckDuckGo Search** | ≥ 8.1 | Agentin internet-hakutyökalu |
| **uv** | ≥ 0.11.12 | Python-paketinhallinta |

---

## Tekijät

**Suvi Niemi, Teo Juurinen, Mikko Valkealahti, Juhani Rautio**
