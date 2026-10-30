"""Lettura delle credenziali di Spaggiari da `schooltools.env`."""

import subprocess
from dataclasses import dataclass
from os import environ
from pathlib import Path

PERCORSO_PREDEFINITO = Path("schooltools.env")

CHIAVE_UTENTE = "SPAGGIARI_UTENTE"
CHIAVE_PASSWORD = "SPAGGIARI_PASSWORD"  # noqa: S105
CHIAVE_COMANDO = "SPAGGIARI_PASSWORD_COMANDO"

MODELLO = f"""\
{CHIAVE_UTENTE}=il-tuo-codice-personale
{CHIAVE_PASSWORD}=la-tua-password
"""


class CredenzialiMancantiError(Exception):
    """Le credenziali non sono state trovate o sono incomplete."""


@dataclass(frozen=True, slots=True)
class Credenziali:
    """Utente e password con cui autenticarsi su Spaggiari."""

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


def password_da_comando(comando: str) -> str:
    """La password stampata su stdout da un comando della shell.

    Il comando eredita terminale, stdin e stderr: un gestore di password che
    chiede la sua password principale (come `keepassxc-cli`) puo' farlo. Della
    sua uscita si toglie solo il fine riga finale.

    Args:
        comando: Riga da far eseguire alla shell.

    Returns:
        La password stampata dal comando.

    Raises:
        CredenzialiMancantiError: Se il comando fallisce o non stampa niente.
    """
    # shell=True e' voluto: il comando lo scrive l'utente nel proprio
    # schooltools.env, e cosi' puo' usare pipe e virgolette come nel terminale.
    esito = subprocess.run(  # noqa: S602
        comando, shell=True, stdout=subprocess.PIPE, text=True, check=False
    )
    if esito.returncode != 0:
        raise CredenzialiMancantiError(
            f"Il comando in {CHIAVE_COMANDO} e' uscito con codice {esito.returncode}"
        )
    password = esito.stdout.rstrip("\r\n")
    if not password:
        raise CredenzialiMancantiError(f"Il comando in {CHIAVE_COMANDO} non ha stampato niente")
    return password


def carica_credenziali(percorso: Path = PERCORSO_PREDEFINITO) -> Credenziali:
    """Le credenziali di Spaggiari, lette dal file indicato.

    Le variabili d'ambiente `SPAGGIARI_UTENTE` e `SPAGGIARI_PASSWORD` fanno da
    alternativa quando il file non esiste o non contiene la voce cercata. Se
    la password manca sia nel file sia nell'ambiente, la si chiede al comando
    in `SPAGGIARI_PASSWORD_COMANDO` (anche questo dal file o dall'ambiente).

    Args:
        percorso: File `.env` da cui leggere le credenziali.

    Returns:
        Le credenziali trovate.

    Raises:
        CredenzialiMancantiError: Se utente o password restano vuoti, o se il
            comando della password fallisce.
    """
    valori: dict[str, str] = {}
    if percorso.is_file():
        valori = leggi_env(percorso.read_text(encoding="utf-8"))

    utente = valori.get(CHIAVE_UTENTE) or environ.get(CHIAVE_UTENTE, "")
    password = valori.get(CHIAVE_PASSWORD) or environ.get(CHIAVE_PASSWORD, "")
    comando = valori.get(CHIAVE_COMANDO) or environ.get(CHIAVE_COMANDO, "")
    if utente and not password and comando:
        password = password_da_comando(comando)

    if not utente or not password:
        raise CredenzialiMancantiError(
            f"Credenziali non trovate: crea il file {percorso} con dentro\n\n{MODELLO}"
        )
    return Credenziali(utente=utente, password=password)
