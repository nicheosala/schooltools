from pathlib import Path

import pytest

from schooltools.config import (
    CHIAVE_PASSWORD,
    CHIAVE_UTENTE,
    CredenzialiMancanti,
    carica_credenziali,
    leggi_env,
)


def test_leggi_env_ignora_commenti_e_righe_vuote() -> None:
    testo = "# commento\n\nA=1\n  B = 2  \nsenza_uguale\n"
    assert leggi_env(testo) == {"A": "1", "B": "2"}


def test_leggi_env_toglie_apici_e_export() -> None:
    testo = "export A='ciao'\nB=\"mondo\"\n"
    assert leggi_env(testo) == {"A": "ciao", "B": "mondo"}


def test_leggi_env_conserva_gli_uguali_nel_valore() -> None:
    assert leggi_env("A=b=c")["A"] == "b=c"


def test_carica_credenziali_dal_file(tmp_path: Path) -> None:
    percorso = tmp_path / "credenziali.env"
    percorso.write_text(f"{CHIAVE_UTENTE}=prof\n{CHIAVE_PASSWORD}=segreta\n")

    credenziali = carica_credenziali(percorso)

    assert credenziali.utente == "prof"
    assert credenziali.password == "segreta"


def test_carica_credenziali_dalle_variabili_ambiente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(CHIAVE_UTENTE, "prof")
    monkeypatch.setenv(CHIAVE_PASSWORD, "segreta")

    assert carica_credenziali(tmp_path / "assente.env").utente == "prof"


def test_carica_credenziali_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(CHIAVE_PASSWORD, raising=False)
    percorso = tmp_path / "credenziali.env"
    percorso.write_text(f"{CHIAVE_UTENTE}=prof\n")

    with pytest.raises(CredenzialiMancanti, match=r"credenziali\.env"):
        carica_credenziali(percorso)
