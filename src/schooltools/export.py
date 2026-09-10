"""Scrittura degli elenchi di studenti in un file xlsx."""

from re import sub
from typing import TYPE_CHECKING

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from schooltools.parsing import abbrevia
from schooltools.students import dividi_nome

if TYPE_CHECKING:
    from collections.abc import Container, Iterable, Mapping, Sequence
    from pathlib import Path

    from openpyxl.worksheet.worksheet import Worksheet

INTESTAZIONI = ("Cognome", "Nome")
LUNGHEZZA_MASSIMA_FOGLIO = 31
CARATTERI_VIETATI = r"[\[\]:*?/\\]"


def nome_foglio(nome: str, usati: Container[str] = ()) -> str:
    """Adatta il nome di una classe ai limiti dei titoli di foglio xlsx.

    Toglie i caratteri che xlsx vieta, accorcia il nome alla sola sigla se
    supera i 31 caratteri consentiti e, se il titolo e' gia' occupato, ci
    aggiunge un numero progressivo.

    Args:
        nome: Nome della classe da usare come titolo.
        usati: Titoli gia' assegnati ad altri fogli della stessa cartella.

    Returns:
        Un titolo valido e non ancora usato.

    Raises:
        ValueError: Se le prime 99 varianti numerate sono tutte occupate.
    """
    pulito = sub(CARATTERI_VIETATI, " ", nome)
    pulito = " ".join(pulito.split()).strip("'") or "Classe"
    if len(pulito) > LUNGHEZZA_MASSIMA_FOGLIO:
        pulito = abbrevia(pulito)
    troncato = pulito[:LUNGHEZZA_MASSIMA_FOGLIO]
    if troncato not in usati:
        return troncato

    for n in range(2, 100):
        suffisso = f" ({n})"
        candidato = pulito[: LUNGHEZZA_MASSIMA_FOGLIO - len(suffisso)] + suffisso
        if candidato not in usati:
            return candidato
    raise ValueError(f"Impossibile trovare un nome di foglio libero per {nome!r}")


def scrivi_xlsx(percorso: Path, classi: Mapping[str, Sequence[str]]) -> Path:
    """Scrive un foglio per classe, con una riga per studente."""
    if not classi:
        raise ValueError("Nessuna classe da scrivere")

    cartella = Workbook()
    predefinito = cartella.active
    if predefinito is not None:
        cartella.remove(predefinito)

    usati: list[str] = []
    for classe, studenti in classi.items():
        titolo = nome_foglio(classe, usati)
        usati.append(titolo)
        _scrivi_foglio(cartella.create_sheet(titolo), studenti)

    percorso.parent.mkdir(parents=True, exist_ok=True)
    cartella.save(percorso)
    return percorso


def _scrivi_foglio(foglio: Worksheet, studenti: Iterable[str]) -> None:
    foglio.append(list(INTESTAZIONI))
    for cella in foglio[1]:
        cella.font = Font(bold=True)

    for studente in studenti:
        foglio.append(list(dividi_nome(studente)))

    foglio.freeze_panes = "A2"
    for i, intestazione in enumerate(INTESTAZIONI, 1):
        larghezza = max(
            [len(intestazione)] + [len(str(c.value or "")) for c in foglio[get_column_letter(i)]]
        )
        foglio.column_dimensions[get_column_letter(i)].width = larghezza + 2
