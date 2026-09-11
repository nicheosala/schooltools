"""Test dell'estrazione dei dati dalle pagine HTML di ClasseViva."""

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


def test_parse_studenti_legge_i_nomi(registro_html: str) -> None:
    """I nomi dell'elenco vengono letti nell'ordine in cui compaiono."""
    assert parse_studenti(registro_html) == [
        "Rossi Giulio",
        "D'Agostino Maria Luisa",
        "Verdi Anna",
    ]


def test_parse_studenti_ignora_la_data_di_nascita(registro_html: str) -> None:
    """Della cella si prende il nome, non la data di nascita che lo accompagna."""
    assert all("2010" not in s for s in parse_studenti(registro_html))


def test_parse_studenti_su_pagina_senza_elenco() -> None:
    """Una pagina senza elenco da' una lista vuota, non un errore."""
    assert parse_studenti("<html><body>niente</body></html>") == []


def test_parse_nome_classe_e_abbreviato(registro_html: str) -> None:
    """Dall'intestazione della pagina si ricava la sola sigla della classe."""
    assert parse_nome_classe(registro_html) == "1E LSA"


def test_parse_nome_classe_assente() -> None:
    """Senza intestazione della classe il nome e' `None`."""
    assert parse_nome_classe("<html></html>") is None


def test_parse_classi_legge_il_menu(registro_html: str) -> None:
    """Il menu a tendina del registro da' tutte le classi, senza ripetizioni."""
    classi = parse_classi(registro_html)

    assert Classe(id="2078364", nome="1E LSA") in classi
    assert [c.nome for c in classi] == [
        "1E LSA",
        "5E LSA",
        "2E LSA",
        "3ELSA",
        "4ELSA",
        "3F LSA",
        "4F",
    ]
    assert len(classi) == len({c.id for c in classi})
    assert len(classi) == 7


def test_parse_classi_senza_menu_usa_la_classe_corrente() -> None:
    """Un docente con una classe sola non ha il menu: vale la classe della pagina."""
    html = """
    <div id="classe_change">3F LSA</div>
    <a href="regclasse.php?granular=g&classe_id=999&gruppo_id=">granulare</a>
    """
    assert parse_classi(html) == [Classe(id="999", nome="3F LSA")]


def test_parse_classi_scarta_i_collegamenti_senza_id() -> None:
    """Un collegamento con `classe_id` vuoto non descrive una classe."""
    html = """
    <div id="lista_classi">
      <a href="regclasse.php?classe_id=&gruppo_id=">vuota</a>
      <a href="regclasse.php?classe_id=12&gruppo_id=">1A</a>
    </div>
    """
    assert parse_classi(html) == [Classe(id="12", nome="1A")]


def test_parse_classi_pagina_vuota() -> None:
    """Senza menu ne' intestazione non si trova nessuna classe."""
    assert parse_classi("<html></html>") == []


def test_parse_classi_dalla_pagina_di_selezione(selezione_html: str) -> None:
    """Anche i riquadri della pagina di selezione danno codici e identificativi."""
    classi = parse_classi(selezione_html)

    assert classi == [Classe(id="111", nome="1E"), Classe(id="222", nome="3ELSA")]


def test_parse_classi_ignora_i_collegamenti_senza_title() -> None:
    """Sulla pagina di selezione conta il collegamento col `title`, non quello di servizio."""
    html = """
    <a href="regclasse.php?classe_id=111&gruppo_id="
       title="Visualizza il registro elettronico della classe 1 E">1E</a>
    <a href="regclasse.php?classe_id=222&gruppo_id=">Registro</a>
    """
    assert parse_classi(html) == [Classe(id="111", nome="1E")]


def test_dividi_nome() -> None:
    """La prima parola e' il cognome, tutto il resto e' il nome."""
    assert dividi_nome("Rossi Giulio") == ("Rossi", "Giulio")
    assert dividi_nome("D'Agostino Maria Luisa") == ("D'Agostino", "Maria Luisa")
    assert dividi_nome("") == ("", "")


def test_abbrevia_tiene_il_codice_della_classe() -> None:
    """Del nome restano l'anno e le sigle brevi, non la descrizione del corso."""
    assert abbrevia("1E LSA LICEO SCIENTIFICO OPZIONE SCIENZE APPLICATE") == "1E LSA"
    assert abbrevia("3ELSA LICEO SCIENTIFICO OPZIONE SCIENZE APPLICATE") == "3ELSA"
    assert abbrevia("4F SCIENTIFICO - OPZIONE SCIENZE APPLICATE") == "4F"
    assert abbrevia("2 AFM AMMINISTRAZIONE FINANZA E MARKETING") == "2 AFM"


def test_abbrevia_lascia_stare_i_nomi_gia_corti() -> None:
    """Un nome fatto di sola sigla passa invariato."""
    assert abbrevia("1E") == "1E"
    assert abbrevia("3F LSA") == "3F LSA"


def test_sigla_classe_toglie_gli_spazi_interni() -> None:
    """La sigla e' il codice tutto attaccato, comunque sia scritto il nome."""
    assert sigla_classe("1A LL LICEO LINGUISTICO NUOVO ORDINAMENTO") == "1ALL"
    assert sigla_classe("2 AFM AMMINISTRAZIONE FINANZA E MARKETING") == "2AFM"
    assert sigla_classe("1E LSA") == "1ELSA"
    assert sigla_classe("3ELSA") == "3ELSA"


def test_sigla_classe_senza_un_codice_da_isolare() -> None:
    """Un nome che non comincia con l'anno non e' un codice: resta com'e'."""
    assert sigla_classe("LICEO  SCIENTIFICO") == "LICEO SCIENTIFICO"
    assert sigla_classe("  ") == ""


def test_abbrevia_senza_numero_iniziale() -> None:
    """Senza numero iniziale non c'e' codice da isolare: il nome resta com'e'."""
    assert abbrevia("LICEO SCIENTIFICO") == "LICEO SCIENTIFICO"
    assert abbrevia("") == ""


def test_parse_account_legge_i_profili() -> None:
    """Dal dialogo si leggono uid e descrizione, con gli spazi normalizzati."""
    html = """
    <div class="item" x-account="uno">Scuola A</div>
    <div class="item" x-account="due">  Scuola   B  </div>
    """
    assert parse_account(html) == [
        Account(uid="uno", descrizione="Scuola A"),
        Account(uid="due", descrizione="Scuola B"),
    ]


def test_parse_account_ripiega_sull_uid_se_manca_la_descrizione() -> None:
    """Un profilo senza testo si presenta col proprio uid."""
    assert parse_account('<div x-account="uno"></div>') == [Account(uid="uno", descrizione="uno")]


def test_parse_account_scarta_le_voci_senza_uid() -> None:
    """Le voci senza un `x-account` utile non sono profili."""
    html = '<div x-account="">vuota</div><div>niente</div>'
    assert parse_account(html) == []


def test_parse_account_dialogo_vuoto() -> None:
    """Un dialogo senza profili da' una lista vuota."""
    assert parse_account("<html></html>") == []
