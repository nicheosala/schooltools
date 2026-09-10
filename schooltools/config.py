"""Lettura delle credenziali di Spaggiari da `credenziali.env`."""

from dataclasses import dataclass
from os import environ
from pathlib import Path

PERCORSO_PREDEFINITO = Path("credenziali.env")

CHIAVE_UTENTE = "SPAGGIARI_UTENTE"
CHIAVE_PASSWORD = "SPAGGIARI_PASSWORD"

MODELLO = f"""\
{CHIAVE_UTENTE}=il-tuo-codice-personale
{CHIAVE_PASSWORD}=la-tua-password
"""


class CredenzialiMancanti(Exception):
    """Le credenziali non sono state trovate o sono incomplete."""


@dataclass(frozen=True, slots=True)
class Credenziali:
    utente: str
    password: str


def leggi_env(testo: str) -> dict[str, str]:
    """Interpreta il contenuto di un file `.env` (righe `CHIAVE=valore`)."""

    valori: dict[str, str] = {}
    for riga in testo.splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga:
            continue
        chiave, _, valore = riga.partition("=")
        chiave = chiave.removeprefix("export ").strip()
        valore = valore.strip()
        if len(valore) >= 2 and valore[0] == valore[-1] and valore[0] in "\"'":
            valore = valore[1:-1]
        if chiave:
            valori[chiave] = valore
    return valori


def carica_credenziali(percorso: Path = PERCORSO_PREDEFINITO) -> Credenziali:
    """Le credenziali lette dal file indicato, con le variabili d'ambiente
    come alternativa se il file non esiste o non le contiene."""

    valori: dict[str, str] = {}
    if percorso.is_file():
        valori = leggi_env(percorso.read_text(encoding="utf-8"))

    utente = valori.get(CHIAVE_UTENTE) or environ.get(CHIAVE_UTENTE, "")
    password = valori.get(CHIAVE_PASSWORD) or environ.get(CHIAVE_PASSWORD, "")

    if not utente or not password:
        raise CredenzialiMancanti(
            f"Credenziali non trovate: crea il file {percorso} con dentro\n\n{MODELLO}"
        )
    return Credenziali(utente=utente, password=password)
