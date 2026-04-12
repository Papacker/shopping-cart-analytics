# Projektiopinnot 1: Datan hallinta

Tämän kurssin repon löydät osoitteesta: [https://gitlab.dclabra.fi/jaakkovan/projektiopinnot-1-datan-hallinta-ttm24sai](https://gitlab.dclabra.fi/jaakkovan/projektiopinnot-1-datan-hallinta-ttm24sai)

Reppu: [https://reppu.kamk.fi/course/view.php?id=1214](https://reppu.kamk.fi/course/view.php?id=1214)
Easy enroll: [https://reppu.kamk.fi/enrol/easy/index.php](https://reppu.kamk.fi/enrol/easy/index.php) -> **7j8tzq**

## Sisällysluettelo

1. [Projektiopinnot 1: Datan hallinta](#projektiopinnot-1-datan-hallinta)
2. [Dokumentaation tuottaminen](#dokumentaation-tuottaminen)
3. [Projekti 1 suunnitelma](#projekti-1-suunnitelma)
4. [Liiketoimintahyödyt](#liiketoimintahyödyt)
5. [Toteutus](#toteutus)
6. [Scrum-viitekehys, vastuut ja laatu](#scrum-viitekehys-vastuut-ja-laatu)
7. [Työkalut](#työkalut)

# Dokumentaation tuottaminen

Projektin dokumentaatio kirjoitetaan Markdown-kielellä hyödyntäen [Material for Mkdocs](https://squidfunk.github.io/mkdocs-material/) -kirjastoa.

Tässä muutamia esimerkkejä Material for Mkdocs -kirjaston mahdollistamista muotoiluista.

 - [Kaaviot](https://squidfunk.github.io/mkdocs-material/reference/diagrams/)
 - [Taulukot](https://squidfunk.github.io/mkdocs-material/reference/data-tables/)
 - [Kuvat](https://squidfunk.github.io/mkdocs-material/reference/images/)
 - [Koodilohkot](https://squidfunk.github.io/mkdocs-material/reference/code-blocks/)

Kattavan listauksen ominaisuuksista löydät osoitteesta [https://squidfunk.github.io/mkdocs-material/reference/](https://squidfunk.github.io/mkdocs-material/reference/).

!!! Yhteensopivuus
    Huomattakoon, ettei Material for Mkdocs ole 100% yhteensopiva aiemmin käyttämämme HedgeDocin kanssa ([https://gitlab.dclabra.fi/wiki](https://gitlab.dclabra.fi/wiki)), mutta voit kirjoittaa dokumentteja wikissä ja kopioida niiden markdown-koodin tänne. Voit myös linkittää tästä dokumentaatiosta ulkoiseen wiki-dokumenttiin, mutta huolehdi että wiki-dokumentti on Locked-tilasssa!

Moi maailma!

## Projekti 1 suunnitelma

Projektin tavoitteena on rakentaa skaalautuva järjestelmäinfrastruktuuri massiivisen UWB-paikannusdatan hallintaan ja analysointiin. Jalostamalla tätä dataa ("anonyymi data") selvitetään muun muassa seuraavia asioita:

- Reitit jota asiakkaat kulkevat kaupassa
- Asioinnin kokonaiskesto
- Asiakassegmentit käyttäytymisen perusteella
- Kassojen ruuhkautumisen seuranta
- Viikonpäivän, kellonajan, sään ja pyhäpäivien vaikutus asiakasmääriin
- Asiakkaiden pysähdykset, kauanko viipyvät tietyillä osastoilla tai hyllyillä

## Liiketoimintahyödyt

Ratkaisu tarjoaa liiketoiminnalle data-analyysien kautta suoraa lisäarvoa:

- Tuotteiden sijoittelu (optimaalisuus)
- Ristiinmyynnin optimointi
- Henkilökunnan tarpeen ennakointi
- Mahdollisuus linkittää ostoihin kassajärjestelmässä

## Toteutus

Raakadatan hallinta toteutetaan kontitetussa ympäristössä (Docker, MariaDB, JupyterLab). Varsinainen datan hyödyntäminen nivoo yhteen analyysin ja esitystavan:

- Automatisoidut raportit vai asiakkaalle mahdollisuus hakea tietokannasta tiettyjä tietoja tiettynä aikana
- Visualisointi: esimerkiksi Heatmap, joka näyttää miten myymälässä liikutaan

## Scrum-viitekehys, vastuut ja laatu

Tiimi toimii itseohjautuvana yksikkönä Scrum-viitekehyksessä. Korkean laadun varmistamiseksi noudatetaan seuraavaa Definition of Done (DoD):
- Koodi noudattaa PEP 8 -tyyliohjetta ja koodauskieli on englanti
- Koodi on tarkistettu staattisella analyysilla (Pylint)
- Kriittiset funktiot on katettu yksikkötesteillä
- Kaikki tekniset ratkaisut ja analyysitulokset on dokumentoitu Markdown-muodossa

## Työkalut

Projektin eri osa-alueet toteutetaan nk. "agenttityyppien" avulla:
- ETL-prosessi eli datan puhdistus
- Tietokannan mallinnus
- Markdown-dokumentin tuottaminen
- Datan visualisointi ("Ali Baba agentti")
- Testaus
- Käyttöliittymä?

**Muut menetelmät ja ympäristöt:**
- Lähdekoodi ja versiohallinta: Gitlab
- Ajanhallinta: Clockify
- Editorit: Wakatime, Koodieditori
- Ympäristö: Docker, MariaDB, JupyterLab
- DCLabra: [iamai-workspace](https://disco.dclabra.fi/@Papacker/team-2-laitetaan-parastamme)

Ajantasaiset sprinttitavoitteet löytyvät GitLabin Issue Boardilta.

### ADR-0001: Agenttien orkestrointikehyksen valinta

## Status 
**Valittu projektin alussa 25.3.2026**

## Konteksti 
CrewAI valittiin projektin pohjaksi idean pohjalta, että on olemassa useampi agentti. Siinä missä yksi agentti suorittaisi kaikki toiminnot, crewai jakaa useammalle agentille pieniä palasia tehtäviä jakaen kuormitusta. Tällä menetelmällä voidaan käyttää agentteja datan käsittelyyn, analysointiin, dokumentointiin, testaamiseen ja liiketoimintaan. Luotettava työkalu ja arkkitehtuuri näiden agenttien työnkulun koordinointiin josta vastaa orkestraattori.

## CrewAI 
CrewAI on framework, jossa agentit ryhmitellään "miehistöksi" (crew), joille annetaan yhteinen tavoite ja tehtävät.
-   Hyödyt: 
- 	Nopea ottaa käyttöön.
-	Agentit osaavat itsenäisesti keskustella, delegoida ja jakaa tehtäviä sisäänrakennettujen roolien (esim. Manager) avulla.
-	Haitat: 
-	Kehittäjällä on vähemmän tarkkaa kontrollia siihen, missä järjestyksessä ja miten agentit asioita käsittelevät.
-	Tiukasti vaiheistetun ketjun pakottaminen voi olla hankalaa.
## Päätös
Tämän hetkisen tilanteen mukaan CrewAI pysyy vaihtoehtona, mahdollisesti harkitaan myöhemmin, jos tämä malli ei toimi projektin toimeksiannon huomioiden halutulla tavalla.
## 
Seuraukset 
## Hyödyt 

## Haitat

### ADR-0002: ETL-putki datan käsittelyyn

## Status 
**Hyväksytty 25.3.2026**
Konteksti 
Raakadata sisältää virheitä ja kohinaa, joten se täytyy käsitellä ennen analyysiä. Hyödyllinen työkalu raakadatan muuttamisessa liiketoimintatiedoksi, poistamalla ylimääräisen epäkelvollisen ja duplikaatit datan joukosta.
Vaihtoehdot 
-	Analysoidaan suoraan CSV:stä
-	Tallennetaan ilman siivousta
-	ETL-prosessi

## Päätös 
Valitaan ETL (Extract, Transform, Load) -putki sen käytettävyyden vuoksí.
## Seuraukset 

## Hyödyt 
-	Parempi datan laatu
-	Toistettava prosessi
-	Standardisoi datan ja suodattaa vain tarpeelliset tiedostot.
Haitat 
•	Uusi koodattava tiedosto projektia varten, lisäten kehitystyötä.
### ADR-0003: DuckDB projektin tietokantana

## Status 
**Hyväksytty 2.4.2026**

## Konteksti 

Projektissa käsitellään suuria määriä UWB-paikannusdataa CSV-tiedostoista. Data tulee esikäsitellä ja tallentaa tehokkaasti analyysiä varten. Tarvitaan tietokantaratkaisu, joka tukee suuria datamääriä, SQL-kyselyitä ja toimii hyvin Docker-ympäristössä.
Vaihtoehdot 
-	SQLite: Kevyt, mutta ei skaalaudu hyvin suurille datamäärille
-	PostgreSQL: Tehokas, mutta raskaampi käyttöönottaa
-	MariaDB: Tasapainoinen suorituskyky ja helppo käyttöönotto

## Päätös 
DuckDB:n hyödyt ovat tämänkaltaisen datan käsittelyssä verrattuna muihin paremmat siivotun datan tallennukseen ja analysointiin, joten päädyimme tähän päätökseen.
Seuraukset 
Hyödyt 
-	Mahdollistaa tehokkaan datan tallennuksen ja haun
-	Tukee monipuolisia SQL-kyselyitä analyysiin
-	Toimii hyvin Docker-ympäristössä

## Haitat 
-	Lisää järjestelmän monimutkaisuutta verrattuna kevyempiin ratkaisuihin

### ADR-0004: Docker konttien käyttö kehitysympäristössä

## Status 
**Hyväksytty 9.4.2026**

## Konteksti 

Projektissa käytetään useita komponentteja, kuten tietokantaa ja analyysityökaluja, joiden asentaminen ja konfigurointi voi vaihdella eri kehittäjien ympäristöissä. Tarvitaan yhtenäinen tapa hallita kehitysympäristöä. Vaihtoehtona Docker-konttien käytölle oli toteuttaa projekti kokonaan koulun tarjoamassa Disco-ympäristössä (https://disco.dclabra.fi/workspaces), jossa osa tarvittavista työkaluista on valmiiksi saatavilla. Vielä mietinnässä  käytetäänkö tätä vai koulun discopalvelinta.
Vaihtoehdot 
-	Disco-ympäristö: Valmiiksi konfiguroitu ympäristö, mutta riippuvuus ulkoisesta palvelusta
-	Paikallinen asennus: Joustava, mutta vaikea pitää yhtenäisenä kaikilla kehittäjillä
-	Docker-kontit: Yhtenäinen ja siirrettävä ratkaisu
Päätös 
Valitaan Docker konttien käyttö kehitysympäristön hallintaan.

## Seuraukset 

## Hyödyt 

-	Yhtenäinen ympäristö kaikille kehittäjille
-	Helppo käyttöönotto
-	Riippuvuudet hallittavissa

## Haitat 

-	Vaatii Dockerin asennuksen kaikille kehittäjille
Analysoida asiakkaan tuottamaa UWB-paikannusdataa. Toteuttaa Streamlit-järjestelmä sisätilapaikannusdatan automaattiseen käsittelyyn, tallennukseen ja analysointiin..

### ADR-0005: Jupyter Notebook datan tutkimiseen

## Status 

**Hyväksytty 25.3.2026**

## Konteksti 

Datan analyysi vaatii iteratiivista työskentelyä ja visualisointia.
Vaihtoehdot 
-	Python-skriptit: Selkeitä, mutta vähemmän interaktiivisia
Päätös 
Jupyter Notebook ja pandas kirjasto valitaan analyysin kehittämiseen.
Seuraukset 
Hyödyt 
-	Nopea kokeilu ja visualisointi
-	Sopii ETL-kehitykseen
Haitat 
-	Koodi voi hajautua

### ADR-0006: Antigravity agenttipohjaisen kehityksen ympäristönä

## Status

**Hyväksytty 2.4.2026**

## Konteksti 

Projektissa halutaan automatisoida ohjelmointityötä agenttien avulla. VSC:n yhteensopivuus uusien työkalujen kanssa ei välttämättä toimi yhtä hyvin kuin käyttäen Antigravityä.
Vaihtoehdot 
-	Manuaalinen kehitys
Päätös 
Valitaan Antigravity agenttipohjaisen kehityksen ympäristöksi.
Seuraukset 
Hyödyt 
-	Nopeuttaa kehitystä
-	Tukee automatisointia
-	Kitkaton skaalautuvuus
Haitat 
-	Vaatii uuden opiskelua
-	Saattaa lisää kompleksisuutta