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