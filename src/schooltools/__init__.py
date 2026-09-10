"""Strumenti per gestire gli elenchi degli studenti del registro Spaggiari."""

from schooltools.config import Credenziali, carica_credenziali
from schooltools.export import scrivi_xlsx
from schooltools.parsing import (
    Account,
    Classe,
    abbrevia,
    parse_account,
    parse_classi,
    parse_nome_classe,
    parse_studenti,
)
from schooltools.spaggiari import LoginError, Registro, RegistroError
from schooltools.students import (
    create_groups,
    create_random_groups,
    dividi_nome,
    extract,
    print_groups,
    read_from_csv,
    register,
    sanitize,
    write_to_csv,
)

__all__ = [
    "Account",
    "Classe",
    "Credenziali",
    "LoginError",
    "Registro",
    "RegistroError",
    "abbrevia",
    "carica_credenziali",
    "create_groups",
    "create_random_groups",
    "dividi_nome",
    "extract",
    "parse_account",
    "parse_classi",
    "parse_nome_classe",
    "parse_studenti",
    "print_groups",
    "read_from_csv",
    "register",
    "sanitize",
    "scrivi_xlsx",
    "write_to_csv",
]
