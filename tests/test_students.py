"""Test del tracciato di importazione utenti di Microsoft 365."""

from schooltools.students import (
    CAMPI_UTENTI,
    Studente,
    capitalizza,
    indirizzo,
    riga_utente,
    sanitize,
)


def test_sanitize() -> None:
    """Apostrofi, punti e spazi spariscono e il resto passa in minuscolo."""
    assert sanitize("D'Agostino") == "dagostino"
    assert sanitize("A.B.") == "ab"
    assert sanitize("De Luca") == "deluca"


def test_capitalizza() -> None:
    """Un nome tutto maiuscolo torna con le sole iniziali maiuscole."""
    assert capitalizza("ROSSI") == "Rossi"
    assert capitalizza("D'AGOSTINO MARIA LUISA") == "D'Agostino Maria Luisa"
    assert capitalizza("") == ""


def test_capitalizza_lascia_stare_chi_ha_gia_delle_minuscole() -> None:
    """Le parole gia' scritte a mano non vengono raddrizzate."""
    assert capitalizza("de Luca") == "de Luca"
    assert capitalizza("McDonald ROSSI") == "McDonald Rossi"


def test_indirizzo() -> None:
    """L'indirizzo non ha spazi, nemmeno con nomi o cognomi composti."""
    assert indirizzo("Maria Luisa", "De Luca") == "marialuisa.deluca@istitutobachelet.edu.it"


def test_riga_utente_mette_la_classe_nel_reparto() -> None:
    """La classe finisce nel reparto, cioe' il campo su cui si raggruppa in Teams."""
    riga = riga_utente(Studente(nome="Giulio", cognome="Rossi", classe="1E LSA"))

    assert len(riga) == len(CAMPI_UTENTI)
    assert dict(zip(CAMPI_UTENTI, riga, strict=True)) == {
        "Nome utente": "giulio.rossi@istitutobachelet.edu.it",
        "Nome": "Giulio",
        "Cognome": "Rossi",
        "Nome visualizzato": "Giulio Rossi",
        "Posizione": "Studente",
        "Reparto": "1ELSA",
        **dict.fromkeys(CAMPI_UTENTI[6:], ""),
    }


def test_riga_utente_da_un_elenco_in_maiuscolo() -> None:
    """Nomi in maiuscolo e classe per esteso arrivano nella forma da portale."""
    riga = riga_utente(
        Studente(
            nome="MARIA LUISA",
            cognome="D'AGOSTINO",
            classe="1A LL LICEO LINGUISTICO NUOVO ORDINAMENTO",
        )
    )

    assert riga[:6] == [
        "marialuisa.dagostino@istitutobachelet.edu.it",
        "Maria Luisa",
        "D'Agostino",
        "Maria Luisa D'Agostino",
        "Studente",
        "1ALL",
    ]


def test_riga_utente_senza_classe() -> None:
    """Senza classe il reparto resta vuoto, come gli altri campi non usati."""
    riga = riga_utente(Studente(nome="Anna", cognome="Verdi"))

    assert riga[CAMPI_UTENTI.index("Reparto")] == ""
