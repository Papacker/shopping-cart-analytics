# Demoilua

[TOC]

# Projekti

Projektin nimi: UWB-paikannustietojen ETL-prosessi, analysointi ja visualisointi käyttöliittymän kautta
Toimeksiantaja: Jaakko Vanhala
Tiimi: Laitetaan parastamme
Kurssi: Dataprojekti 1, 2026 

## Tiimi ja Roolit

Esitelkää tiimi ja miten kiertävä Scrum-malli toteutui käytännössä.

| Jäsen | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 | Sprint 7 | Sprint 8 |
| -------- | -------- | -------- |-------- |-------- |-------- |-------- |-------- |
| Juhani Rautio | Scrummaster | PO  | Dev | Dev | PO | Dev | Scrummaster | Dev |
| Teo Juurinen | PO | Scrummaster | Dev | Dev | Dev | Scrummaster | Dev | PO |
| Mikko Valkealahti | Dev | Dev | PO | Scrummaster | Scrummaster | Dev | PO | Dev |
| Suvi Niemi | Dev | Dev | Scrummaster | PO | Dev | PO | Dev | Scrummaster |
| Jussi Seppänen | Dev | Dev | - | - | - | - | - | - |

## Ongelma ja Ratkaisu (Business Case)
Mitä yritys pyysi ja mitä teitte?

* Toimeksianto: Kauppias on kerännyt dataa ostoskärryjen liikkeistä myymälässä UWB-teknologian avulla, mutta ei ole varma miten sitä voisi hyödyntää.
* Ratkaisun tavoite: Datan analysointi ja visualisointi siten, että se auttaa kauppiasta tekemään parempia päätöksiä liiketoiminnassaan. Tavoitteena on luoda työkalu, joka on helppokäyttöinen ja vastaa kauppiaan kysymyksiin datasta.
* MVP: Mikä on tämänhetkisen prototyypin tärkein ominaisuus?
Tavoitteen kannalta olennaisen datan visualisointi luonnollisella kielellä esitettyjen kyselyjen perusteella sekä suositukset liiketoiminnan kehittämiseen. 

## Tekninen Toteutus (Pipeline)
Miten data liikkui ja mitä sille tapahtui?

Data-arkkitehtuuri:
* Datan keruu: Raakadata on tallennettuna kärrykohtaisiin csv-tiedostoihin. Tiedostoja on 31 kpl ja ne on tallennettu koulun palvelimelle.
* Datan esikäsittely ja siivous (KRIITTINEN VAIHE):
    * Miksi siivottiin? 
    Tiedostoissa oli yhteensä noin 140 miljoonaa riviä, joten raakadatan käsittely olisi ollut erittäin hidasta. Yksi rivi sisälsi ostoskärryn paikannuskoordinaatit ja aikaleiman sekä Q- ja Z-arvon. Z-arvo kertoi paikannussignaalin korkeuden (kerros) ja Q-arvo laadun. Jotta datasta saatiin järkevä analysoitava kokonaisuus, joka vastaisi luotettavasti asiakaskäyttäytymistä, raakadatasta täytyi siivota pois epäoleelliset tiedot sekä mahdolliset virheet, jotta lopputulos olisi luotettava.  
    * Mitä siivottiin? 
    1. Q-arvo ja Z-arvosarakkeet. Z-arvolla ei ollut merkitystä, koska myymälä oli yhdessä kerroksessa. Q-arvon mittaristo ei puolestaan ollut tiedossa. 
    2. Negatiiviset koordinaatit (x-akselin 0-linja = kassojen keskilinja, y-koordinaatiston 0 = vasen yläkulma)
    3. Liikkeet myymälän ulkopuolella ja dead zone -alueilla, koska niillä ei ollut liiketoiminnallista arvoa. 
    4. Hajanaiset signaalit, jotka eivät muodostaneet ostossessiota eli alkaneet sisäänkäynniltä ja päättyneet kassalle.
    5. Aukioloaikojen ulkopuoliset signaalit. 
    6. Liian nopeat siirtymät
    7. Sessiot, jotka jäivät myymälän sisällä alle 50 metrin pituisiksi. 
    
    Siivouksen jälkeen datasta noin 93 % oli epäoleellista tai virheellistä. Suurin osa epäoleellisesta datasta oli hajanaisia signaaleja, latauspisteessä vietettyä aikaa, liian lyhyitä sessioita ja kohinaa. 

    * Millä siivottiin?
    Siivous suoritettiin python-ohjelmointikielellä ja pandas-kirjastolla. Siivottu data tallennettiin parquet-muodossa DuckDB-tietokantaan.
* Datan validointi (Miten varmistimme, ettei validia dataa poistunut?):
    * Rivinmäärien vertailu: Tarkistimme shape-metodilla datamäärän ennen ja jälkeen jokaisen operaation.
    * Tilastollinen vertailu: Vertasimme keskiarvoja ja hajontaa (mean, std) ennen ja jälkeen siivouksen varmistaaksemme, ettei datan jakauma vääristynyt.
    * Logitus: Kirjasimme ylös jokaisen hylätyn rivin syyn (esim. dropped_rows.csv), jotta ne voitiin pistokokein tarkistaa.
    * Audit Trail: Kaikki raakadatasta tunnistetut trajektorit (istunnot) kirjataan joko Visit- (validit) tai Quality-tauluun (invalidit). Suppilokaavio visualisoi tämän prosessin läpinäkyvästi.
    * Yksikkötestit: Kirjoitimme testejä, jotka varmistivat, että tunnetusti validit testisyötteet läpäisevät filtterit.
* Testausstrategia ja toteutus:
* AI-arkkitehtuuri: (Mitä mallia tai malleja ja algoritmeja käytettiin ja miksi?)
    * Missä niitä käytettiin
    * Miten validoitiin että hallusinaatiota ei esiinny?
    * Koulutettiinko omia malleja?
    * Käytettiinko jotain frameworkkeja?
* Teknologiapino: Python, GitLab CI/CD, Pandas, NumPy, Matplotlib, Seaborn, DuckDB, CrewAI, Jupyter Lab, Streamlit



## ADR (Architecture Decision Records)

Miksi valitsitte juuri nämä työkalut tai menetelmät?

* Päätös 1: Kirjastovalinta
    * Konteksti: Tarvitsimme työkalun suuren datamäärän käsittelyyn.
    * Päätös: Valitsimme Pandas-kirjaston.
    * Perustelu: Laaja dokumentaatio, tiimin aiempi osaaminen ja hyvä tuki AI-malleille.
* Päätös 2: Mallin valinta
    * Konteksti: Ennustettava arvo oli jatkuva (hinta/aika).
    * Päätös: Lineaarinen regressio vs. Random Forest.
    * Perustelu: Päädyimme Random Forestiin, koska se sieti paremmin datassa olevaa kohinaa (outliers).
* Päätös 3: Infrastruktuuri
    * Päätös: GitLab CI/CD:n käyttö testauksessa.
    * Perustelu: Automaatio varmisti, ettei uusi koodi rikkonut olemassa olevaa data-pipelinea.

## LIVE-DEMO
Näyttäkää koodin toimivuus tai lopputuote

* Skenaario: "Käyttäjä haluaa tietää X..."
* Suoritus: Ajakaa skripti / näyttäkää Dashboard.
* Tulos: Mitä malli ennusti tai analysoi?

## Projektinhallinta ja Metriikat (Data-ohjattu tiimi)
Näyttäkää, miten käytitte työkaluja projektin seurantaan

Työmäärät (Clockify / WakaTime)
* Kokonais tunnit: [X] h
* Työn jakautuminen: * Kehitys (Dev): [X]%
* Datan käsittely: [X]%
* Dokumentointi & Palaverit: [X]%
* WakaTime-huomioita: Mikä tiedostotyyppi tai kirjasto vei eniten aikaa?

Git-työskentely (GitLab)
* Commitit: [X] kpl
* Branch-malli: (Esim. Feature branching)
* Merge Requestit: Miten katselmoinnit hoidettiin?
* Burn chartit

Työkuorman jakautuminen (gitlab analyze)

## Oppiminen ja Retrospektiivi
Mitä jäi käteen?

* Mikä onnistui? (Esim. "Saimme CI/CD-putken toimimaan ensiyrittämällä")
* Mikä oli haastavaa? (Esim. "Datan laatu oli odotettua huonompaa")
* Jatkoehdotus: Jos projekti jatkuisi ensi vuonna, mitä tekisitte seuraavaksi?

## Linkit

GitLab Repositorio
https://gitlab.dclabra.fi/ttm25sai/projekti1/projektiopinnot-1-datan-hallinta-laitetaan-parastamme
Oppimispäiväkirjat

© 2026 Laitetaan parastamme | Kajaanin Ammattikorkeakoulu | Insinöörikoulutus

