# Agenttiarkkitehtuurin laajentaminen: Datanpurkajasta strategiseksi konsultiksi

Tässä projektin vaiheessa päätin laajentaa sovelluksen olemassa olevaa CrewAI-agenttia. Tavoitteena oli siirtyä pelkästä yhden kysymyksen ("one-shot") vastaajasta kohti aidosti vuorovaikutteista ja älykästä tekoälykumppania.

## Mitä tehtiin?
Teknologiapinossa (Streamlit, FastAPI, CrewAI) tehtiin seuraavat kriittiset muutokset:

1. **Jatkuvan keskustelumuistin (Chat History) rakentaminen:** 
   Streamlit-käyttöliittymä tallensi aiemmin keskustelun vain visuaalisesti, mutta backend ja tekoäly aloittivat joka pyynnön tyhjältä pöydältä. Muutin ohjelmointirajapintaa (API) siten, että koko keskustelun historia välitetään joka kerta eteenpäin suoraan agentin tehtävänantoon.
2. **Uuden asiantuntijaroolin luominen:** 
   CrewAI-tiimiin lisättiin uusi agentti nimeltä "Kaupan liiketoiminnan kehittäjä". Tämä rooli ohjeistettiin toimimaan kokeneena vähittäiskaupan asiantuntijana, ei koodarina tai data-analyytikkona.
3. **Älykäs mallin reititys:** 
   Rakensin dynaamisen logiikan, joka lukee käyttäjän syötteen. Jos kysymyksessä on sanoja kuten "kehitys", "idea", "strategia" tai "miten", kysymys reititetään automaattisesti Kaupan kehittäjä -agentille. Data- ja koodauskysymykset ohjautuvat vanhaan tapaan analyytikoille.
4. **Internet-haku työkalupakkiin:** 
   Asensin järjestelmään DuckDuckGo-hakulaajennuksen ja tein agentille uuden Python-työkalun (`search_web`).

## Miksi tehtiin?
Alkuperäinen agentti oli suljetussa järjestelmässä elävä kova-koodattu apulainen. Se osasi lukea tietokannasta ostoskärryjen UWB-koordinaatit ja kertoa tulokset, mutta siltä puuttui täysin **konteksti** aiemmista kysymyksistä ja **ymmärrys** siitä, mitä datalla voi todellisuudessa tehdä. 

Kun halutaan kehittää liiketoimintaa, pelkkä "osastolla 3 on ruuhkaa" ei riitä. Tekoälyn pitää osata kertoa *miten* kyseistä ruuhkaa pitäisi hallita tai hyödyntää. Tämä vaatii asiantuntijapersoonaa ja jatkuvaa dialogia.

## Mitä haetaan?
Näiden muutosten myötä ohjelmasta haetaan aitoa liiketoiminnallista arvoa. Kun järjestelmä tietää oman kaupan analytiikan (tietokannan suora esihaku), muistaa käyttäjän edellisen jatkokysymyksen (Chat history) ja pystyy lukemaan internetistä vähittäiskaupan uusimmat trendit (DDG Search Tool), se voi tarjota myymäläpäällikölle valmiiksi pureskeltuja, dataan pohjautuvia kehitysideoita.

Agentti ei ole enää pelkkä "käyttöliittymä tietokantaan", vaan aktiivinen konsultti.
