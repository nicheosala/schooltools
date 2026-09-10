"""Test della lettura delle credenziali da file .env e da variabili d'ambiente."""

from typing import TYPE_CHECKING

import pytest

from schooltools.config import (
    CHIAVE_PASSWORD,
    CHIAVE_UTENTE,
    CredenzialiMancantiError,
    carica_credenziali,
    leggi_env,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_leggi_env_ignora_commenti_e_righe_vuote() -> None:
    """Commenti, righe vuote e righe senza `=` non finiscono fra i valori."""
    testo = "# commento\n\nA=1\n  B = 2  \nsenza_uguale\n"
    assert leggi_env(testo) == {"A": "1", "B": "2"}


def test_leggi_env_toglie_apici_e_export() -> None:
    """Il prefisso `export` e gli apici attorno al valore vengono tolti."""
    testo = "export A='ciao'\nB=\"mondo\"\n"
    assert leggi_env(testo) == {"A": "ciao", "B": "mondo"}


def test_leggi_env_conserva_gli_uguali_nel_valore() -> None:
    """La riga si divide sul primo `=`: gli altri restano dentro il valore."""
    assert leggi_env("A=b=c")["A"] == "b=c"


def test_carica_credenziali_dal_file(tmp_path: Path) -> None:
    """Utente e password vengono presi dal file indicato."""
    percorso = tmp_path / "schooltools.env"
    percorso.write_text(f"{CHIAVE_UTENTE}=prof\n{CHIAVE_PASSWORD}=segreta\n")

    credenziali = carica_credenziali(percorso)

    assert credenziali.utente == "prof"
    assert credenziali.password == "segreta"


def test_carica_credenziali_dalle_variabili_ambiente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Se il file non c'e' si ripiega sulle variabili d'ambiente."""
    monkeypatch.setenv(CHIAVE_UTENTE, "prof")
    monkeypatch.setenv(CHIAVE_PASSWORD, "segreta")

    assert carica_credenziali(tmp_path / "assente.env").utente == "prof"


def test_carica_credenziali_incomplete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Con la sola utente manca la password: l'errore cita il file da compilare."""
    monkeypatch.delenv(CHIAVE_PASSWORD, raising=False)
    percorso = tmp_path / "schooltools.env"
    percorso.write_text(f"{CHIAVE_UTENTE}=prof\n")

    with pytest.raises(CredenzialiMancantiError, match=r"schooltools\.env"):
        carica_credenziali(percorso)
