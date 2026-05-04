# Demoilua

[TOC]

# Projekti

Projektin nimi: [TÄHÄN PROJEKTIN NIMI]
Toimeksiantaja: [Yrityksen nimi]
Tiimi: [Tiimin nimi / Numero]
Kurssi: [Kurssin nimi / Numero]

## Tiimi ja Roolit

Esitelkää tiimi ja miten kiertävä Scrum-malli toteutui käytännössä.

| Jäsen | Sprint 1 | Sprint 2 |
| -------- | -------- | -------- |
| Opiskelija A | PO | Dev   |

## Ongelma ja Ratkaisu (Business Case)
Mitä yritys pyysi ja mitä teitte?

* Toimeksianto: Lyhyt kuvaus yrityksen haasteesta.
* Ratkaisun tavoite: Miten tekoäly/data-analyysi auttaa tässä haasteessa?
* MVP: Mikä on tämänhetkisen prototyypin tärkein ominaisuus?

## Tekninen Toteutus (Pipeline)
Miten data liikkui ja mitä sille tapahtui?

Data-arkkitehtuuri:
* Datan keruu: (Mistä data tuli? API, CSV, SQL?)
* Datan esikäsittely ja siivous (KRIITTINEN VAIHE):
    * Miksi siivottiin? (Esim. puuttuvat arvot, virheelliset tyypit, outliers.)
    * Mitä siivottiin? (Esim. "Poistimme 15% riveistä, joista puuttui hintatieto".)
    * Millä siivottiin? (Esim. Pandas, NumPy, Regex.)
* Datan validointi (Miten varmistimme, ettei validia dataa poistunut?):
    * Rivinmäärien vertailu: Tarkistimme shape-metodilla datamäärän ennen ja jälkeen jokaisen operaation.
    * Tilastollinen vertailu: Vertasimme keskiarvoja ja hajontaa (mean, std) ennen ja jälkeen siivouksen varmistaaksemme, ettei datan jakauma vääristynyt.
    * Logitus: Kirjasimme ylös jokaisen hylätyn rivin syyn (esim. dropped_rows.csv), jotta ne voitiin pistokokein tarkistaa.
    * Audit Trail: Kaikki raakadatasta tunnistetut trajektorit (istunnot) kirjataan joko Visit- (validit) tai Quality-tauluun (invalidit). Suppilokaavio visualisoi tämän prosessin läpinäkyvästi.
    * Yksikkötestit: Kirjoitimme testejä, jotka varmistivat, että tunnetusti validit testisyötteet läpäisevät filtterit.
* AI-malli: (Mitä mallia tai malleja ja algoritmeja käytettiin ja miksi?)
    * Missä niitä käytettiin?
    * Miten validoitiin että hallusinaatiota ei esiinny?
    * Koulutettiinko omia malleja?
    * Käytettiinko jotain frameworkkeja?
* Teknologiapino: Python, GitLab CI/CD, Pandas, Scikit-learn, NumPy, etc



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