"""Test della sessione sul registro, con un trasporto HTTP finto."""

from collections.abc import Callable, Sequence

import pytest
from httpx2 import Client, MockTransport, Request, Response

from schooltools.parsing import Classe
from schooltools.spaggiari import (
    URL_REGISTRO,
    Account,
    LoginError,
    Registro,
    RegistroError,
)

Gestore = Callable[[Request], Response]


def _registro(gestore: Gestore) -> Registro:
    """Un registro le cui richieste finiscono al gestore invece che in rete."""
    return Registro(Client(transport=MockTransport(gestore), follow_redirects=True))


def _auth(**campi: object) -> dict[str, object]:
    """La risposta JSON dell'API di autenticazione, con i campi indicati."""
    return {"data": {"auth": {"errors": [], **campi}, "pfolio": False}}


def _dialogo(*account: tuple[str, str]) -> dict[str, object]:
    """La risposta JSON che propone di scegliere fra piu' profili."""
    voci = "".join(f'<div class="item" x-account="{uid}">{nome}</div>' for uid, nome in account)
    return {
        "data": {
            "auth": {"verified": True, "loggedIn": False, "errors": []},
            "pfolio": {"filteredDialogHtml": f"<div>{voci}</div>"},
        }
    }


def test_login_riuscito() -> None:
    """Il login visita la pagina di accesso e poi l'API di autenticazione."""
    visitati: list[str] = []

    def gestore(richiesta: Request) -> Response:
        visitati.append(f"{richiesta.method} {richiesta.url.path}")
        if richiesta.method == "POST":
            assert b"uid=prof" in richiesta.content
            assert b"target=cvv" in richiesta.content
            return Response(200, json=_auth(verified=True, loggedIn=True))
        return Response(200, html="<html></html>")

    with _registro(gestore) as registro:
        registro.login("prof", "segreta")

    assert visitati == [
        "GET /home/app/default/login.php",
        "POST /auth-p7/app/default/AuthApi4.php",
    ]


def test_login_con_credenziali_sbagliate() -> None:
    """Le credenziali rifiutate diventano un errore che riporta il messaggio del registro."""

    def gestore(richiesta: Request) -> Response:
        if richiesta.method == "POST":
            return Response(
                200,
                json={
                    "data": {
                        "auth": {
                            "verified": False,
                            "loggedIn": False,
                            "errors": ["Identificativo o password errati"],
                        },
                        "pfolio": False,
                    }
                },
            )
        return Response(200, html="<html></html>")

    with (
        _registro(gestore) as registro,
        pytest.raises(LoginError, match="Identificativo o password errati"),
    ):
        registro.login("prof", "sbagliata")


def test_login_con_piu_profili_usa_quello_scelto() -> None:
    """Con piu' profili si consulta chi sceglie e si rifa' il login col suo uid."""
    inviati: list[bytes] = []

    def gestore(richiesta: Request) -> Response:
        if richiesta.method != "POST":
            return Response(200, html="<html></html>")
        inviati.append(richiesta.content)
        if richiesta.url.params.get("a") == "aLoginPwd":
            return Response(200, json=_dialogo(("uno", "Scuola A"), ("due", "Scuola B")))
        return Response(200, json=_auth(verified=True, loggedIn=True))

    def scegli(account: Sequence[Account]) -> Account:
        assert [a.descrizione for a in account] == ["Scuola A", "Scuola B"]
        return account[1]

    with _registro(gestore) as registro:
        registro.login("prof", "segreta", scegli_account=scegli)

    assert b"uid=due" in inviati[1]


def test_login_predefinito_prende_il_primo_profilo() -> None:
    """Senza una funzione di scelta si prende il primo profilo proposto."""
    inviati: list[bytes] = []

    def gestore(richiesta: Request) -> Response:
        if richiesta.method != "POST":
            return Response(200, html="<html></html>")
        inviati.append(richiesta.content)
        if richiesta.url.params.get("a") == "aLoginPwd":
            return Response(200, json=_dialogo(("uno", "Scuola A")))
        return Response(200, json=_auth(verified=True, loggedIn=True))

    with _registro(gestore) as registro:
        registro.login("prof", "segreta")

    assert b"uid=uno" in inviati[1]


def test_login_senza_profili_proposti() -> None:
    """Il registro chiede di scegliere un profilo ma non ne propone nessuno."""

    def gestore(richiesta: Request) -> Response:
        if richiesta.method == "POST":
            return Response(200, json=_auth(verified=True, loggedIn=False))
        return Response(200, html="<html></html>")

    with (
        _registro(gestore) as registro,
        pytest.raises(LoginError, match="profilo"),
    ):
        registro.login("prof", "segreta")


def test_login_con_risposta_non_json() -> None:
    """Una risposta che non e' JSON diventa un errore di login leggibile."""

    def gestore(richiesta: Request) -> Response:
        if richiesta.method == "POST":
            return Response(200, text="manutenzione in corso")
        return Response(200, html="<html></html>")

    with (
        _registro(gestore) as registro,
        pytest.raises(LoginError, match="Risposta inattesa"),
    ):
        registro.login("prof", "segreta")


def test_login_con_errore_di_rete() -> None:
    """Uno stato HTTP di errore diventa un errore che cita l'indirizzo chiamato."""
    with (
        _registro(lambda _richiesta: Response(500)) as registro,
        pytest.raises(RegistroError, match="Errore di rete"),
    ):
        registro.login("prof", "segreta")


def test_classi_dalla_pagina_di_selezione(selezione_html: str) -> None:
    """Senza classe_id il registro serve la pagina di selezione, e le classi si leggono li'."""
    with _registro(lambda _richiesta: Response(200, html=selezione_html)) as registro:
        classi = registro.classi()

    assert classi == [Classe(id="111", nome="1E"), Classe(id="222", nome="3ELSA")]


def test_classi(registro_html: str) -> None:
    """Dal menu del registro di classe si ricavano tutte le classi del docente."""
    with _registro(lambda _richiesta: Response(200, html=registro_html)) as registro:
        classi = registro.classi()

    assert len(classi) == 7
    assert classi[0].id == "2078364"


def test_classi_su_pagina_vuota() -> None:
    """Nessuna classe trovata: la sessione e' probabilmente scaduta, e lo si dice."""
    with (
        _registro(lambda _richiesta: Response(200, html="<html></html>")) as registro,
        pytest.raises(RegistroError, match="Nessuna classe"),
    ):
        registro.classi()


def test_studenti_chiede_la_classe_giusta(registro_html: str) -> None:
    """La richiesta porta il classe_id chiesto e la risposta diventa l'elenco dei nomi."""
    richieste: list[Request] = []

    def gestore(richiesta: Request) -> Response:
        richieste.append(richiesta)
        return Response(200, html=registro_html)

    with _registro(gestore) as registro:
        studenti = registro.studenti(Classe(id="42", nome="1A"))

    assert richieste[0].url.params.get("classe_id") == "42"
    assert studenti == ["Rossi Giulio", "D'Agostino Maria Luisa", "Verdi Anna"]


def test_sessione_scaduta() -> None:
    """Un rimbalzo sulla pagina di login segnala che la sessione non vale piu'."""

    def gestore(richiesta: Request) -> Response:
        if "regclasse" in richiesta.url.path:
            return Response(302, headers={"Location": "/home/app/default/login.php"})
        return Response(200, html="<html></html>")

    with (
        _registro(gestore) as registro,
        pytest.raises(RegistroError, match="Sessione non valida"),
    ):
        registro.studenti(Classe(id="42", nome="1A"))


def test_url_registro_e_quello_del_cvv() -> None:
    """L'indirizzo del registro punta all'applicativo cvv di Spaggiari."""
    assert URL_REGISTRO.endswith("/cvv/app/default/regclasse.php")
