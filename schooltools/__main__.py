from csv import DictWriter, reader
from random import randint, sample
from typing import Iterable, Iterator

from bs4 import BeautifulSoup
from more_itertools import chunked


def scrape(html_file_path: str) -> list[str]:

    students: list[str] = []

    with open(html_file_path, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        for s in soup.find_all("td", "elenco_studenti"):
            student = s.find("div").text.title()
            students.append(student)

    return students


def write_to_csv(csv_file_path: str, students: list[str]) -> None:
    with open(csv_file_path, "w", newline="") as f:
        w = DictWriter(f, ["Studente"])
        for s in students:
            w.writerow({"Studente": s})


def read_from_csv(csv_file_path: str) -> list[str]:
    with open(csv_file_path, "r") as file:
        return [s for [s] in reader(file)]


def create_groups(students: Iterable[str], d: int) -> Iterator[list[str]]:
    return chunked(students, d)


def create_random_groups(students: Iterable[str], d: int) -> Iterator[list[str]]:
    return create_groups(sample(students, len(students)), d)


def print_groups(groups: Iterable[list[str]]) -> None:
    print()
    for i, g in enumerate(groups, 1):
        print(f"Gruppo {i}")
        for member in g:
            print(member)
        print()


def extract(students: Iterable[str]) -> str:
    r = randint(0, len(students) - 1)
    return students[r]


def register(students: list[str]) -> None:
    for i, s in enumerate(students, 1):
        print(i, s)


if __name__ == "__main__":

    students = scrape("schooltools/classi/2clsa.html")
    groups = create_random_groups(students, 3)
    print_groups(groups)
