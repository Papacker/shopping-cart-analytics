# Projektiblogi: UWB-paikannusdatan analytiikka ja käyttöliittymä

Tämä dokumentti kokoaa yhteen projektimme teknisen toteutuksen. Käymme läpi massiivisen raakadatan esikäsittelyn, laadunvalvonnan askel askeleelta, ohjelmiston arkkitehtuurin sekä analytiikka-dashboardin käyttöliittymäsuunnittelun kehitysvaiheet. Tämä dokumentti toimii myös kattavana teknisenä käsikirjana projektin jatkokehittäjille.

## Datan esikäsittely ja laadunvalvonta

Lähtökohtana projektissa oli 31 raakaa CSV-tiedostoa, jotka sisälsivät yhteensä noin 140 miljoonaa riviä ostoskärryihin kiinnitettyjen UWB-sensorien paikannusdataa.

### Suorituskyky ja rinnakkaisajo
Koska datamäärä oli suuri, perinteinen peräkkäinen käsittely muodostui pullonkaulaksi. Jaoimme datan luvun ja puhdistuksen rinnakkaisiin prosesseihin (`ProcessPoolExecutor`). Lisäksi siirryimme käyttämään DuckDB:tä, joka pystyy lukemaan suuria CSV-tiedostoja huomattavasti nopeammin ja tehokkaammin kuin perinteinen Pandas. Näillä optimoinneilla koko aineiston prosessointiaika puristettiin alle 30 sekuntiin (aiemman usean minuutin sijaan).

### Datan siivous ja esikäsittely
UWB-data on luonnostaan kohinaista: se sisältää virheellisiä signaaliheijastuksia, paikallaan seisovia kärryjä ja kaupan aukioloaikojen ulkopuolista liikennettä. Data puhdistettiin seuraavien tiukkojen vaiheiden kautta:

1. **Spatiaalinen siivous:** Suodatimme ensin pois kaikki myymälän fyysisten rajojen ulkopuolelle (esim. ulos tai varastoon) osuvat koordinaatit sekä määritellyt "kuolleet alueet" kuten latauspisteet.
2. **Sessiointi (Vierailujen tunnistaminen):** Jatkuva datapistevirta pilkottiin erillisiksi asiointikerroiksi aikakatkosten perusteella. Jos kärry on yli 5 minuuttia paikallaan tai yhteys katkeaa, järjestelmä päättelee vanhan asioinnin päättyneen ja aloittaa uuden.
3. **Liikesuodatus:** Paikannusvirheistä johtuvat epäluonnolliset nopeudet (yli 10 km/h "hypyt" myymälän sisällä) tunnistettiin ja poistettiin.
4. **Validointi ja suodatus:** Lopuksi kukin tunnistettu istunto ajettiin validointisuodattimen läpi. Hylkäsimme suoraan sessiot, jotka olivat liian lyhyitä (alle 50 pistettä), kestivät epärealistisen pitkään (esim. hylätty kärry), tai tapahtuivat yöaikaan kun kauppa on kiinni.

### Logitus, validointi ja Audit Trail
Datan validoinnin periaatteena oli 100-prosenttinen läpinäkyvyys. Halusimme tietää tarkalleen, miksi valtava määrä raakarivejä hylättiin. 

Käytimme "Audit Trail" -lähestymistapaa: ETL-putki ei poista virheelliseksi tunnistettua dataa hiljaisesti, vaan kukin hylätty sessio tallennetaan tietokannan erilliseen `Quality`-tauluun tarkan hylkäyssyyn (esim. "TOO_FEW_POINTS" tai "SESSION_TOO_LONG") kera. Tämän ansiosta pystyimme seuraamaan terminaalin lokituksista jatkuvasti prosessin onnistumista, rivimäärien pudotusprosentteja (hyväksymisprosentti asettui n. 8,3 %:iin) ja vakuuttumaan siitä, että poistettu data oli aidosti arvotonta kohinaa.

---

## Projektin arkkitehtuuri ja kansiorakenne

Projekti on refaktoroitu noudattamaan modulaarista Clean Architecture -periaatetta, mikä takaa vakauden ja helpottaa jatkokehitystä:

* **`main.py`**: Ohjelmiston sydän ja ETL-putken sisääntulopiste. Hoitaa rinnakkaisajon (Multiprocessing), ohjaa datan puhdistusta ja populoi DuckDB-tietokannan.
* **`config/`**: Asetustiedostot, kuten `store_config.py`, joka sisältää myymälän fyysiset mitat, osastojen koordinaatit (bounding boxes) ja kalibrointiparametrit.
* **`src/app.py`**: Käyttöliittymän reititin (router). Sitoo dashboardin komponentit yhteen, mutta ei sisällä raskasta datalogiikkaa. Pitää sisällään macOS-eristyksen, jotta ETL-työläiset eivät lataa Streamlitiä taustalla.
* **`src/processor.py`**: Sisältää raskaat laskentafunktiot (esim. sessiointi ja spatiaaliset tietokantaliitokset DuckDB:llä).
* **`src/queries.py`**: Eristetty datakerros. Kaikki käyttöliittymän tarvitsemat SQL-haut on keskitetty tänne.
* **`src/charts.py`**: Visualisointikirjasto, joka pitää sisällään Matplotlib-kuvaajien piirtologiikan tyyliteltynä tumman teeman mukaisesti.
* **`src/tabs/`**: Dashboardin varsinaiset käyttöliittymänäkymät. Jokainen välilehti (esim. `tab2_traffic.py`) on oma eristetty yksikkönsä, mikä tekee koodista selkeälukuista.
* **`src/style.css`**: Globaali tyylitiedosto, joka vastaa sovelluksen visuaalisesta modernista ilmeestä.
* **`docs/`**: Projektin dokumentaatiokansio (blogi, lokit ja vaatimusmäärittelyt).

---

## Käyttöliittymäsuunnittelu ja arkkitehtuuri

Käyttöliittymän rakentaminen Streamlitin päälle tapahtui iteratiivisesti. Alkuperäinen tavoite oli esittää data yksinkertaisesti, mutta projektin edetessä tavoitteeksi muodostui ammattimainen, modulaarinen ja visuaalisesti miellyttävä työkalu. 

### 1. Monoliitista modulaariseksi arkkitehtuuriksi
Aluksi koko sovellus asui yhdessä suuressa `app.py`-tiedostossa. Kun ominaisuuksia tuli lisää, tiedosto kasvoi yli 700-riviseksi, mikä vaikeutti ylläpitoa. Refaktoroimme sovelluksen PEP8-periaatteiden mukaisesti pilkkomalla datanhaut, kuvaajat ja itse välilehdet omiin tiedostoihinsa. Tämä eriyttäminen paransi vakautta huomattavasti ja poisti ilmenneitä Streamlitin ajo-ongelmia eristämällä datan käsittelyn käyttöliittymäkomponenteista.

### 2. Visuaalinen ilme ja teemoitus
Käyttöliittymän ulkoasu vietiin pois Streamlitin oletustyylistä kohti modernimpaa "dark mode" -teemaa. 
- Erotimme kaikki tyylit omaan `style.css`-tiedostoon.
- Hyödynsimme lasimaisia pintoja (glassmorphism), pehmeitä gradientteja ja yhdenmukaista typografiaa tuodaksemme käyttöliittymään selkeyttä ja ammattimaisuutta.
- Varmistimme, että visuaaliset elementit asettuvat ruudulle selkeästi myös erikokoisilla näytöillä (`width='stretch'`).

---

## Dashboardin välilehdet ja niiden taustalogiikka

Lopullinen käyttöliittymä jakautuu kuuteen välilehteen. Jotta kuka tahansa tiimin jäsen voi jatkokehittää työkaluja, olemme avanneet alle jokaisen välilehden tarkoituksen ja teknisen toimintalogiikan:

### 1. Datan laatu (Health & Quality)
*   **Tarkoitus:** Vastaa kysymykseen, mitä raakadatalle tapahtui ja miksi sitä hylättiin. Varmistaa analytiikan läpinäkyvyyden käyttäjälle.
*   **Tekninen logiikka:** ETL-putki erityisesti `processor.py` vertaa jokaista sessiota sääntöihin. Jos sessio hylätään, funktio palauttaa virhestriingin esim. `TOO_FEW_POINTS`. Nämä kirjataan suoraan DuckDB:n `Quality`-tauluun. Käyttöliittymässä ajetaan yksinkertainen SQL `COUNT()` -ryhmittely `GROUP BY reason`, josta piirretään selkeä vaakapalkkikaavio esittämään osuudet.

### 2. Liikennevirrat (Traffic)
*   **Tarkoitus:** Keskittyy myymälän yleiseen vilkkauteen ja asiointien kestoon. Suodattaa "haamukärryt" ja näyttää kävijämäärät tunneittain ja viikonpäivittäin.
*   **Tekninen logiikka:** Hakee `Visit`-taulusta hyväksytyt asioinnit. SQL-kyselyssä käytetään `EXTRACT(hour FROM start_time)` -funktioita aikasarjojen purkamiseen. Tärkeä logiikka: data suodatetaan erikseen jättämällä yli 2 tuntia kestävät sessiot (mahdolliset latauspisteelle unohtuneet kärryt, jotka läpäisivät ensisuodattimen) pois keskiarvojen laskennasta, jotta tunnusluvut (KPI) pysyvät totuudenmukaisina.

### 3. Kassa- ja osastoanalytiikka (Checkout & Departments)
*   **Tarkoitus:** Sukeltaa asiakkaan reittiin, näyttäen suosituimmat osastot, keskimääräiset viipymät ja eri kassojen käyttöasteet. Sisältää apuna avattavan pohjakartan.
*   **Tekninen logiikka:** Tämä on teknisesti yksi ohjelman raskaimmista laskennoista, mutta se on viety **pois** käyttöliittymästä ETL-vaiheeseen. `processor.py` ajaa spatiaalisen vertailun (x/y pisteet vs. `store_config.py`:n osastojen raatiot eli "bounding boxes") ja yhdistää (JOIN) peräkkäiset samalla alueella tapahtuvat pisteet `ZoneVisit`-riveiksi. UI tekee yksinkertaisia hakuja tähän valmiiseen relaatiotauluun. Näin vältetään käyttöliittymän jäätyminen.

### 4. Kärrydynamiikka (Fleet Dynamics)
*   **Tarkoitus:** Laajentaa työkalun laitteiston huoltoon, näyttämällä yksittäisten ostoskärryjen myymälässä kulkeman kumulatiivisen matkan. Varoittaa yli 50 km kulkeneista kärryistä.
*   **Tekninen logiikka:** SQL-kysely käyttää DuckDB:n analytiikkafunktioita (kuten `LAG() OVER PARTITION`) hakemaan edellisen datapisteen koordinaatit samassa visiitissä. Etäisyys lasketaan suoraan tietokannassa Pythagoraan lauseen avulla (`SQRT(POWER(x - prev_x, 2) + ...)`). Summa jaetaan muuntaen pikselit/sentit kilometreiksi. Tuloksesta piirretään viivakaavio, johon on koodattu visuaalinen katkaisuraja (esim. punainen viiva huoltorajan kohdalle).

### 5. Lämpökartat (Heatmaps)
*   **Tarkoitus:** Piirtää visuaalisesti näyttävän tiheyskartan asiakkaiden liikkumisesta oikean myymäläpohjapiirroksen päälle interaktiivisten aikasäätimien kera.
*   **Tekninen logiikka:** Hyödyntää `Zone`-taulua, josta haetaan kymmeniä tuhansia (sampled) pisteitä kerrallaan valittujen suodattimien perusteella. Kuvaaja (Matplotlib `ax.hist2d`) luo kaksiulotteisen histogrammin, joka peitetään läpinäkyvänä taustakuvan päälle. Koordinaatistot mapataan lennossa yhteen käyttämällä `store_config.py`:ssä määritettyjä origon x/y-koordinaatteja ja skaalauskertoimia (`scale_cm_per_px`), ja käännetään ylösalaisin tarpeen mukaan (`invert_y`).

### 6. Edistynyt analytiikka (Advanced Insights)
*   **Tarkoitus:** Tuo dataputkeen ulkopuolisen ulottuvuuden yhdistämällä sääolosuhteet (lämpötila/sade) kävijämääriin. Näyttää myös myymälän kylmimmät osastot ("dead zones").
*   **Tekninen logiikka:** Tekee Pythonin `requests`-kirjastolla dynaamisen API-pyynnön avoimeen Open-Meteo arkistorajapintaan Järvenpään myymälän koordinaateilla. Parametreina annetaan tietokannan ensimmäisen ja viimeisen visiitin päivämäärät. Palautuva JSON-data parsitaan Pandasin DataFrameksi ja yhdistetään (`pd.merge`) DuckDB:stä haettujen päivittäisten kävijämäärien kanssa. Data visualisoidaan kaksiakselisella (`twinx`) Matplotlib-kaaviolla.

---

## Kehitysloki 

Jotta projektin iteratiivinen kehitys jää talteen, olemme listanneet alle Git-historiaan pohjautuvan kronologisen lokin keskeisimmistä kehitysvaiheistamme (Phases 1-33).

*   **[Phase 1-3] Perusteiden rakentaminen:** Dokumentaation linjaaminen kurssivaatimuksiin. Ensimmäinen Datan laatu -välilehti (Tab 1) rakennettiin validointivaatimusten täyttämiseksi. Tyylittely (`style.css`) eriytettiin monoliitista.
*   **[Expansion Phase 1-6] Analytiikan ja arkkitehtuurin laajennus:** Dashboard jaettiin 6 erilliseen välilehteen ammattimaisuuden korostamiseksi. Rakennettiin ensimmäiset versiot kassa-analytiikasta, kärrydynamiikasta (Pythagoraan lause tietokannassa), Lämpökarttojen aikasuodattimista sekä Open-Meteo Sää-API integraatioista. Tietokantaskeemaan luotiin `Categories`- ja `ZoneVisit`-taulut.
*   **[Expansion Phase 7-10] ETL-suorituskyvyn radikaali optimointi:** Ylipitkien (jopa satojen tuntien) "haamusessioiden" tunnistus ja rajaaminen pois (max 90min). Pythonin rinnakkaisajo (`ProcessPoolExecutor`) otettiin käyttöön, mikä laski 140 miljoonan rivin ajon 3 minuuttista alle 30 sekuntiin. SQL-natiivit spatiaaliset liitokset (joins) implementoitiin siirtäen raskaat silmukat Pythonista DuckDB:n vastuulle.
*   **[Expansion Phase 11-20] Datan siivouksen tiukennus ja UI-logiikan korjaus:** Terminaali puhdistettiin Streamlit-varoituksista. Laadunvalvonnan pie chart vaihdettiin luettavampaan palkkikaavioon. Yksityiskohtainen "Audit Trail" dokumentoitiin osaksi vaatimusmäärittelyitä. Osasto- ja kassaanalytiikasta poistettiin purkkapatentit; se integroitiin onnistuneesti pre-moduloituun `ZoneVisit`-dataan, mikä nopeutti ohjelmaa merkittävästi.
*   **[Expansion Phase 21-30] "The Visual Revolution" ja Liiketoimintametriikat:** Koko dashboard suunniteltiin uudelleen visuaalisesti; käyttöön otettiin neon-värit, lasimaiset paneelit (glassmorphism) ja moderni typografia. Sää-API ja kävijämäärät lokalisoitiin täsmällisesti Tokmanni Järvenpään kohdalle.
*   **[Phase 31-33] Tuotantovalmius (Production Hardening) ja PEP8:** Koodikanta jaettiin lopullisesti paloihin (`src/tabs/`, `src/queries.py` jne.) ja PEP8-varoitusvirheet siivottiin nollaan. macOS-ympäristön aiheuttamat Multiprocessing `spawn`-ongelmat ratkaistiin rakentamalla tiukka `MainProcess`-eristys, mikä lopetti Streamlitin aiheuttamat "NoneType"-kaatumiset tausta-ajoissa. Käyttöliittymä on täysin äänetön komentorivillä, tarjoten vain tyylitellyt etenemispalkit ETL-ajosta.

---

## Yhteenveto

Projektin aikana järjestelmä kehittyi valtavan datamassan raskaasta putkistosta ammattimaiseksi, luotettavaksi ja nopeaksi analytiikka-dashboardiksi. Läpinäkyvä esikäsittely ja tarkka laadunvalvonta takaavat, että esitetty tieto on aitoa liiketoimintadataa. Kun raskas laskenta keskitettiin ETL-vaiheeseen DuckDB-tietokantaan, modulaarinen käyttöliittymä pystyy palvelemaan käyttäjää reaaliaikaisesti ja tarjoamaan rikkaan analyysin asiakaskäyttäytymisestä. Tämä dokumentti tukee vahvasti järjestelmän ylläpitoa ja jatkokehitystä tulevaisuudessa.
