"""Funzioni di utilita' su una lista di studenti."""

from collections.abc import Iterable, Iterator, Sequence
from csv import reader, writer
from random import randint, sample

from more_itertools import chunked

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
    return s.lower().replace("'", "").replace(".", "")


def dividi_nome(studente: str) -> tuple[str, str]:
    """Divide "COGNOME Nome Secondo" in ("COGNOME", "Nome Secondo")."""

    parti = studente.split()
    if not parti:
        return "", ""
    return parti[0], " ".join(parti[1:])


def write_to_csv(csv_file_path: str, students: list[str]) -> None:
    with open(csv_file_path, "w", newline="") as f:
        w = writer(f, delimiter=",")
        w.writerow(CAMPI_CSV)
        for s in students:
            cognome, nome = dividi_nome(s)
            nome_utente = (
                f"{sanitize(nome.replace(' ', ''))}.{sanitize(cognome)}@{DOMINIO}"
            )
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
    with open(csv_file_path) as file:
        return [s for [s] in reader(file)]


def create_groups(students: Iterable[str], d: int) -> Iterator[list[str]]:
    return chunked(students, d)


def create_random_groups(students: Sequence[str], d: int) -> Iterator[list[str]]:
    return create_groups(sample(students, len(students)), d)


def print_groups(groups: Iterable[list[str]]) -> None:
    print()
    for i, g in enumerate(groups, 1):
        print(f"Gruppo {i}")
        for member in g:
            print(member)
        print()


def extract(students: Sequence[str]) -> str:
    r = randint(0, len(students) - 1)
    return students[r]


def register(students: Iterable[str]) -> None:
    for i, s in enumerate(students, 1):
        print(i, s)
