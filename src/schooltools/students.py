"""Funzioni di utilita' su una lista di studenti."""

from csv import reader, writer
from itertools import batched
from pathlib import Path
from random import randint, sample
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

CAMPI_CSV = [
    "Nome utente",
    "Nome",
    "Cognome",
    "Nome visualizzato",
    "Posizione",
    "Reparto",
    "Numero ufficio",
    "Telefono ufficio",
    "Cellulare",
    "Fax",
    "Indirizzo di posta elettronica alternativo",
    "Indirizzo",
    "Città",
    "Stato o provincia",
    "CAP",
    "Paese o area geografica",
]

DOMINIO = "istitutobachelet.edu.it"


def sanitize(s: str) -> str:
    """Riduce una parte di nome alla forma ammessa in un indirizzo di posta.

    Args:
        s: Nome o cognome da ripulire.

    Returns:
        Il testo in minuscolo, senza apostrofi ne' punti.
    """
    return s.lower().replace("'", "").replace(".", "")


def dividi_nome(studente: str) -> tuple[str, str]:
    """Divide "COGNOME Nome Secondo" in ("COGNOME", "Nome Secondo")."""
    parti = studente.split()
    if not parti:
        return "", ""
    return parti[0], " ".join(parti[1:])


def write_to_csv(csv_file_path: str, students: list[str]) -> None:
    """Scrive gli studenti nel CSV di importazione utenti di Microsoft 365.

    Le colonne e il loro ordine sono quelli che il portale si aspetta; a ogni
    studente viene assegnato un indirizzo `nome.cognome@DOMINIO` e la posizione
    "Studente", mentre i campi rimanenti restano vuoti.

    Args:
        csv_file_path: File da scrivere, sovrascritto se esiste.
        students: Studenti nella forma "COGNOME Nome".
    """
    with Path(csv_file_path).open("w", newline="") as f:
        w = writer(f, delimiter=",")
        w.writerow(CAMPI_CSV)
        for s in students:
            cognome, nome = dividi_nome(s)
            nome_utente = f"{sanitize(nome.replace(' ', ''))}.{sanitize(cognome)}@{DOMINIO}"
            w.writerow(
                [
                    nome_utente,
                    nome,
                    cognome,
                    s,
                    "Studente",
                    *[""] * (len(CAMPI_CSV) - 5),
                ]
            )


def read_from_csv(csv_file_path: str) -> list[str]:
    """Legge un elenco di studenti da un CSV di una colonna sola.

    Args:
        csv_file_path: File da leggere.

    Returns:
        Il contenuto dell'unica colonna, una voce per riga.

    Raises:
        ValueError: Se una riga non ha esattamente un campo.
    """
    with Path(csv_file_path).open() as file:
        return [s for [s] in reader(file)]


def create_groups(students: Iterable[str], d: int) -> Iterator[list[str]]:
    """Divide gli studenti in gruppi consecutivi, nell'ordine in cui arrivano.

    Args:
        students: Studenti da dividere.
        d: Quanti studenti per gruppo.

    Returns:
        I gruppi uno dopo l'altro; l'ultimo puo' averne meno di `d`.
    """
    return (list(gruppo) for gruppo in batched(students, d, strict=False))


def create_random_groups(students: Sequence[str], d: int) -> Iterator[list[str]]:
    """Divide gli studenti in gruppi dopo averli mescolati.

    Args:
        students: Studenti da dividere.
        d: Quanti studenti per gruppo.

    Returns:
        I gruppi uno dopo l'altro; l'ultimo puo' averne meno di `d`.
    """
    return create_groups(sample(students, len(students)), d)


def print_groups(groups: Iterable[list[str]]) -> None:
    """Stampa i gruppi numerati, uno per blocco separato da una riga vuota.

    Args:
        groups: Gruppi da stampare.
    """
    print()
    for i, g in enumerate(groups, 1):
        print(f"Gruppo {i}")
        for member in g:
            print(member)
        print()


def extract(students: Sequence[str]) -> str:
    """Sorteggia uno studente, per interrogarlo o per assegnargli un turno.

    Args:
        students: Studenti fra cui sorteggiare.

    Returns:
        Lo studente estratto.

    Raises:
        ValueError: Se l'elenco e' vuoto.
    """
    r = randint(0, len(students) - 1)
    return students[r]


def register(students: Iterable[str]) -> None:
    """Stampa l'elenco degli studenti numerato, come sul registro cartaceo.

    Args:
        students: Studenti da stampare.
    """
    for i, s in enumerate(students, 1):
        print(i, s)
