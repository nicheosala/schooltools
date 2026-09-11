"""Strumenti per gestire gli elenchi degli studenti del registro Spaggiari."""

from schooltools.config import Credenziali, carica_credenziali
from schooltools.export import scrivi_utenti_xlsx, scrivi_xlsx
from schooltools.parsing import (
    Account,
    Classe,
    abbrevia,
    dividi_nome,
    parse_account,
    parse_classi,
    parse_nome_classe,
    parse_studenti,
    sigla_classe,
)
from schooltools.spaggiari import LoginError, Registro, RegistroError
from schooltools.students import (
    Studente,
    capitalizza,
    indirizzo,
    riga_utente,
    sanitize,
)
from schooltools.teams import leggi_origine

__all__ = [
    "Account",
    "Classe",
    "Credenziali",
    "LoginError",
    "Registro",
    "RegistroError",
    "Studente",
    "abbrevia",
    "capitalizza",
    "carica_credenziali",
    "dividi_nome",
    "indirizzo",
    "leggi_origine",
    "parse_account",
    "parse_classi",
    "parse_nome_classe",
    "parse_studenti",
    "riga_utente",
    "sanitize",
    "scrivi_utenti_xlsx",
    "scrivi_xlsx",
    "sigla_classe",
]
