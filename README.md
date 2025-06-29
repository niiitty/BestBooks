# BestBooks
#### Nettisivuprojekti kurssille Tietokannat ja web-ohjelmointi.

Sovelluksen tarkoitus on antaa käyttäjälle mahdollisuus jakaa lukemiaan kirjoja. Kirjoja pystyy löytämään selailemalla etusivua tai hakemalla niitä hakusanoilla. Kirjojen sivuilta voi löytyä kirjailijan lisäksi julkaisuaika sekä sen lajityypit. Kaikki käyttäjät pystyvät antamaan omat arvostelunsa ja arvosanansa kirjasta, jolloin siitä näytetään keskiarvosana.

## Ominaisuudet
- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan kirjoja. Kirjasta löytyy perustiedot kuten nimi, kirjailija ja julkaisuaika.
- Kirjalle pystyy valitsemaan yhden tai useamman lajityypin.
- Käyttäjä näkee sovellukseen lisätyt kirjat etu- sekä käyttäjäsivulta.
- Käyttäjä pystyy hakemaan kirjoja hakusanoilla.
- Käyttäjäsivu näyttää käyttäjän lisäämät kirjat sekä lisättyjen kirjojen määrän.
- Käyttäjä pystyy antamaan kirjalle arvostelun ja arvosanan. Kirjasta näytetään keskiarvosana sekä sen arvostelut.

## Sovelluksen asennus

Asenna `flask`-kirjasto virtuaaliympäristöön:

```
$ pip install flask
```

Voit käynnistää sovelluksen näin:

```
$ flask run
```

Sovellus luo tarvittavat tietokannan taulut käynnistyksessä.

## Toiminta suurella tietomäärällä

`seed.py`-tiedostosta löytyy koodi, joka luo monta käyttäjää, kirjaa sekä arvostelua. Kirjojen lisääjät valitaan satunnaisesti käyttäjistä, ja kaikki arvostelut menevät viimeiseille kirjalle.

Etu-, käyttäjä- ja kirjasivujen sivuttamisen ansiota niiden lataamisessa kestää enintään 0,06 sekuntia. Lisäämällä indeksin tämä laski ~0,002 sekunnin viiveeseen. Toki voi pohtia, onko se sen arvoista, kun tietokanta kasvaa melkein 11 megatavua eli noin 30 %.

Sovelluksen hitain ominaisuus on ehdottomasti sen haku. Äärimmäisillään esimerkiksi haulla `book` sivun lataamisessa kesti  14,91 sekuntia, kun sopivia tuloksia oli 10**6. Kokeilin yhdessä kohtaa Sqliten FTS5-virtuaalitaulua, mutta sillä ei voi etsiä keskeltä otsikkoa `vuoden -> Sadan vuoden yksinäisyys` ja muutenkin se vei noin 10 sekuntia enemmän aikaa sivun lataamiseen.
