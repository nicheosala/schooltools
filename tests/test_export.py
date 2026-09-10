from pathlib import Path

import pytest
from openpyxl import load_workbook

from schooltools.export import INTESTAZIONI, nome_foglio, scrivi_xlsx


def test_nome_foglio_corto_resta_uguale() -> None:
    assert nome_foglio("1A") == "1A"


def test_nome_foglio_abbrevia_i_nomi_lunghi() -> None:
    assert nome_foglio("1E LSA LICEO SCIENTIFICO OPZIONE SCIENZE APPLICATE") == "1E LSA"


def test_nome_foglio_tronca_quando_non_puo_abbreviare() -> None:
    nome = nome_foglio("CORSO SERALE DI INFORMATICA PER ADULTI LAVORATORI")

    assert len(nome) == 31
    assert nome.startswith("CORSO SERALE")


def test_nome_foglio_lascia_stare_i_nomi_gia_corti() -> None:
    assert nome_foglio("3A CORSO SERALE") == "3A CORSO SERALE"


def test_nome_foglio_toglie_i_caratteri_vietati() -> None:
    assert nome_foglio("3A/B: [prova]?*") == "3A B prova"


def test_nome_foglio_evita_i_duplicati() -> None:
    assert nome_foglio("1A", usati=["1A"]) == "1A (2)"
    assert nome_foglio("1A", usati=["1A", "1A (2)"]) == "1A (3)"


def test_nome_foglio_vuoto() -> None:
    assert nome_foglio("   ") == "Classe"


def test_scrivi_xlsx_un_foglio_per_classe(tmp_path: Path) -> None:
    percorso = scrivi_xlsx(
        tmp_path / "studenti.xlsx",
        {"1A": ["Rossi Giulio", "D'Agostino Maria Luisa"], "2B": ["Verdi Anna"]},
    )

    cartella = load_workbook(percorso)
    assert cartella.sheetnames == ["1A", "2B"]

    foglio = cartella["1A"]
    assert [c.value for c in foglio[1]] == list(INTESTAZIONI)
    assert [[c.value for c in riga] for riga in foglio.iter_rows(min_row=2)] == [
        ["Rossi", "Giulio"],
        ["D'Agostino", "Maria Luisa"],
    ]
    assert cartella["2B"].max_row == 2


def test_scrivi_xlsx_classi_con_nome_lungo_e_uguale(tmp_path: Path) -> None:
    lungo = "LICEO SCIENTIFICO OPZIONE SCIENZE APPLICATE"
    percorso = scrivi_xlsx(tmp_path / "s.xlsx", {f"{lungo} A": [], f"{lungo} B": []})

    nomi = load_workbook(percorso).sheetnames
    assert len(nomi) == 2
    assert all(len(n) <= 31 for n in nomi)


def test_scrivi_xlsx_crea_le_cartelle(tmp_path: Path) -> None:
    percorso = scrivi_xlsx(tmp_path / "a" / "b" / "s.xlsx", {"1A": ["Rossi Giulio"]})

    assert percorso.is_file()


def test_scrivi_xlsx_senza_classi(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Nessuna classe"):
        scrivi_xlsx(tmp_path / "s.xlsx", {})
