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

* Toimeksianto: Kauppias on kerännyt dataa ostoskärryjen liikkeistä myymälässä UWB-teknologian avulla, mutta ei ole varma mihin sitä pitäisi käyttää.
* Ratkaisun tavoite: Datan analysointi ja visualisointi siten, että se auttaa kauppiasta ymmärtämään paremmin ostoskärryjen käyttäjien liikkumista myymälässä ja tekemään parempia päätöksiä liiketoiminnassaan. Tavoitteena on luoda työkalu, joka on helppokäyttöinen ja joka auttaa kauppiasta ymmärtämään asiakkaiden käyttäytymistä myymälässä.
* MVP: Mikä on tämänhetkisen prototyypin tärkein ominaisuus?
Tavoitteen kannalta olennaisen datan visualisointi luonnollisella kielellä esitettyjen kyselyjen perusteella sekä suositukset datan hyödyntämiseksi. 

## Tekninen Toteutus (Pipeline)
Miten data liikkui ja mitä sille tapahtui?

Data-arkkitehtuuri:
* Datan keruu: Raakadata on tallennettuna kärrykohtaisiin csv-tiedostoihin. Tiedostoja on 31 kpl ja ne on tallennettu koulun palvelimelle.
* Datan esikäsittely ja siivous (KRIITTINEN VAIHE):
    * Miksi siivottiin? 
    Tiedostoissa oli yhteensä noin 140 miljoonaa riviä, joten raakadatan käsittely olisi ollut erittäin hidasta. Yksi rivi sisälsi ostoskärryn paikannuskoordinaatit ja aikaleiman sekä Q- ja Z-arvon. Z-arvo kertoi paikannussignaalin korkeuden (kerros) ja Q-arvo laadun. Jotta datasta saatiin järkevä analysoitava kokonaisuus, joka vastaisi luotettavasti asiakaskäyttäytymistä, raakadatasta täytyi siivota pois epäoleelliset tiedot sekä mahdolliset virheet, jotta lopputulos olisi luotettava.  
    * Mitä siivottiin? 
    1. Q-arvo ja Z-arvosarakkeet. Q-arvolla ei ollut merkitystä, koska myymälä oli yhdessä kerroksessa. Z-arvon mittaristo ei puolestaan ollut tiedossa. 
    2. Negatiiviset koordinaatit (x-koordinaatiston 0-linja = kassojen keskilinja, y-koordinaatiston 0 = vasen yläkulma)
    3. Liikkeet dead zone -alueilla, koska myymälän ulkopuolisella datalla ei ollut liiketoiminnallista arvoa. 
    4. Hajanaiset signaalit, jotka eivät muodostaneet ostossessiota eli alkaneet sisäänkäynniltä ja päättyneet kassalle.
    5. Aukioloaikojen ulkopuoliset signaalit. 
    6. Liian nopeat siirtymät
    7. Sessiot, jotka jäivät myymälän sisällä alle 50 metrin pituisiksi. 
    
    Siivouksen jälkeen datasta noin 90 % oli epäoleellista tai virheellistä. Suurin osa epäoleellisesta datasta oli hajanaisia signaaleja, liian lyhyitä sessioita ja kohinaa. 

    * Millä siivottiin? (Esim. Pandas, NumPy, Regex.)
* Datan validointi (Miten varmistimme, ettei validia dataa poistunut?):
    * Rivinmäärien vertailu: Tarkistimme shape-metodilla datamäärän ennen ja jälkeen jokaisen operaation.
    * Tilastollinen vertailu: Vertasimme keskiarvoja ja hajontaa (mean, std) ennen ja jälkeen siivouksen varmistaaksemme, ettei datan jakauma vääristynyt.
    * Logitus: Kirjasimme ylös jokaisen hylätyn rivin syyn (esim. dropped_rows.csv), jotta ne voitiin pistokokein tarkistaa.
    * Audit Trail: Kaikki raakadatasta tunnistetut trajektorit (istunnot) kirjataan joko Visit- (validit) tai Quality-tauluun (invalidit). Suppilokaavio visualisoi tämän prosessin läpinäkyvästi.
    * Yksikkötestit: Kirjoitimme testejä, jotka varmistivat, että tunnetusti validit testisyötteet läpäisevät filtterit.
* AI-malli: (Mitä mallia tai malleja ja algoritmeja käytettiin ja miksi?)
    * Missä niitä käytettiin
    * Miten validoitiin että hallusinaatiota ei esiinny?
    * Koulutettiinko omia malleja?
    * Käytettiinko jotain frameworkkeja?
* Teknologiapino: Python, GitLab CI/CD, Pandas, NumPy, Matplotlib, Seaborn,DuckDB, CrewAi, Jupyterlab, Streamlit  



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

© 202X [Tiimin Nimi] | Ammattikorkeakoulu | Insinöörikoulutus

# Ohjeita

Mitä, miksi ja miten?

## Mitä se on?

* Demo on konkreettinen esitys ohjelmiston nykytilasta.
* Se ei ole PowerPoint-esitys, vaan toimivan ohjelmiston näyttämistä aidossa tai sen kaltaisessa ympäristössä.

## Miksi se pidetään? (Välidemo)

* Varhainen palaute: On helpompaa korjata suuntaa nyt kuin kaksi viikkoa ennen julkaisua.
* Luottamuksen rakentaminen: Asiakas tai sidosryhmät näkevät, että budjetille saadaan vastinetta.
* Väärinkäsitysten karsiminen: Teksti speksissä ja koodi ruudulla voivat näyttää erilaisilta eri ihmisten silmissä.

## Miten se toteutetaan? (Välidemo)

* Valmistelu: Valitaan tärkeimmät uudet ominaisuudet (User Stories).
* Livenä näyttäminen: Kehittäjä tai tuoteomistaja (PO) klikkailee sovellusta ja selittää logiikan.
* Keskustelu: Kerätään huomiot: "Tämä on hyvä, mutta voisiko tuo nappi olla selkeämpi?"
* Kirjaaminen: Muutostoiveet viedään backlogille.

## Missä tilassa projekti on tässä vaiheessa? (Välidemo)

* Välidemon kohdalla projekti on yleensä "keskeneräinen mutta toimiva".
* Ydinlogiikka (MVP-taso): Perustoiminnot (kuten sisäänkirjautuminen tai datan haku) yleensä toimivat.
* Käyttöliittymä: Ulkoasu saattaa olla vielä viimeistelemätön (ns. "karvalakkimalli"), mutta polku alusta loppuun on kuljettavissa.
* Tekninen velka: Kaikkea ei ole vielä optimoitu, ja virheiden käsittely voi olla puutteellista.

## Miten päästään lopputulokseen? (Välidemo)
Välidemo toimii ponnahduslautana viimeistelyyn:

* Priorisointi: Demossa tulleet palautteet laitetaan tärkeysjärjestykseen. Kaikkea ei ehkä ehditä tehdä.
* Bugien metsästys: Keskitytään vakauteen.
* Viimeistely (Polishing): Hiotaan käyttöliittymää, animaatioita ja suorituskykyä.
* Hyväksymistestaus (UAT): Käyttäjät testaavat ohjelmiston varmistaakseen, että se täyttää vaatimukset

# Muita huomioita

- Pyrkikää ammattimaiseen otteeseen.
- Demoissa voi ja usein onkin mukana ulkopuolisia.
- Erittäin usein demot ovat arvioitavia kohteita.
- Jokaisen tiimijäsenen tulisi ainakin kerran puhua demon aikana.
- Huomioikaa demoissa se että tiettyjä dokumentteja tai asioita voidaan pyytää erikseen palautettavan tai että keskitytään tiettyihin asioihin.
    - Esimerkiksi voi olla välidemo pelkästään arkkitehtuurista
    - Jos on pyydetty jotain tiettyä - tätä kannattaa esitellä
- Muistakaa että jos sitä ei ole dokumentoitu - sitä ei ole olemassa.