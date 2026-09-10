"""Fixture condivise: le pagine HTML del registro salvate sotto `tests/data/`."""

from pathlib import Path

import pytest

DATI = Path(__file__).parent / "data"


@pytest.fixture
def registro_html() -> str:
    """L'HTML (ridotto e anonimizzato) di una pagina regclasse.php."""
    return (DATI / "registro.html").read_text(encoding="utf-8")


@pytest.fixture
def selezione_html() -> str:
    """L'HTML (ridotto) della pagina di selezione della classe."""
    return (DATI / "selezione.html").read_text(encoding="utf-8")
