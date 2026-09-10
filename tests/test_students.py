"""Test delle utilita' sugli elenchi di studenti."""

from typing import TYPE_CHECKING

from schooltools.students import (
    CAMPI_CSV,
    create_groups,
    dividi_nome,
    read_from_csv,
    sanitize,
    write_to_csv,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_sanitize() -> None:
    """Apostrofi e punti spariscono e il resto passa in minuscolo."""
    assert sanitize("D'Agostino") == "dagostino"
    assert sanitize("A.B.") == "ab"


def test_dividi_nome() -> None:
    """La prima parola e' il cognome, tutto il resto e' il nome."""
    assert dividi_nome("Rossi Giulio") == ("Rossi", "Giulio")
    assert dividi_nome("D'Agostino Maria Luisa") == ("D'Agostino", "Maria Luisa")
    assert dividi_nome("") == ("", "")


def test_write_to_csv(tmp_path: Path) -> None:
    """Il CSV ha le colonne di Microsoft 365 e l'indirizzo ricavato dal nome."""
    percorso = tmp_path / "studenti.csv"

    write_to_csv(str(percorso), ["D'Agostino Maria Luisa"])

    righe = percorso.read_text().splitlines()
    assert righe[0].split(",") == CAMPI_CSV
    campi = righe[1].split(",")
    assert campi[0] == "marialuisa.dagostino@istitutobachelet.edu.it"
    assert campi[1:5] == [
        "Maria Luisa",
        "D'Agostino",
        "D'Agostino Maria Luisa",
        "Studente",
    ]
    assert len(campi) == len(CAMPI_CSV)


def test_read_from_csv(tmp_path: Path) -> None:
    """Un CSV di una colonna sola torna come elenco di nomi."""
    percorso = tmp_path / "nomi.csv"
    percorso.write_text("Rossi Giulio\nVerdi Anna\n")

    assert read_from_csv(str(percorso)) == ["Rossi Giulio", "Verdi Anna"]


def test_create_groups() -> None:
    """I gruppi sono consecutivi e l'ultimo puo' essere piu' corto degli altri."""
    gruppi = list(create_groups(["a", "b", "c", "d", "e"], 2))

    assert gruppi == [["a", "b"], ["c", "d"], ["e"]]
