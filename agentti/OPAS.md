# 1. Projektin ohjekirja

# 🛒 UWB-Myymäläanalytiikka: Agenttien Ohjeistus

Tämä projekti analysoi myymälän IoT-dataa DuckDB:n ja CrewAI-agenttien avulla.

## 🛠️ Ympäristöasetukset
- **LLM:** Ollama (`qwen2.5-coder:7b`)
- **Host:** `http://localhost:11434`
- **Tietokanta:** `database/store.db` (DuckDB)
- **Konfiguraatio:** `config/store_config.py`

## 📂 Hakemistorakenne
- `/agentti`: Agenttien koodit ja työkalut.
- `/agentti/workspace`: Tänne tallentuvat agenttien luomat skriptit ja raportit.
- `/database`: Sisältää `store.db` tiedoston.
- `/config`: Sisältää myymälän koordinaatit ja skaalauskertoimet.

## 📊 Tietokantataulut
- **Zone**: Raakadata (10M+ riviä). Sarakkeet: `x, y, z, timestamp, tag_id`.
- **Quality**: Puhdistettu data, josta lasketaan viipymät ja osastovierailut.

## 🤖 Ohjeet agenteille
1. ÄLÄ etsi tiedostoja juuresta tai `/home`-hakemistosta.
2. Käytä AINA `inspect_schema`-työkalua nähdäksesi taulut.
3. Jos kirjoitat Python-koodia, tallenna se `workspace/`-kansioon.

# 2. Asennusopas

# A. Järjestelmän valmistelu
```
sudo apt update && sudo apt install zstd -y
curl -fsSL https://ollama.com/install.sh | sh
```

# B. Tekoälyn käynnistys

```
# Käynnistä Ollama taustalle
ollama serve & 

# Lataa koodausmalli (n. 4.7 GB)
ollama pull qwen2.5-coder:7b

# C. Python-ympäristön synkronointi (projektin juuressa)
uv sync
```