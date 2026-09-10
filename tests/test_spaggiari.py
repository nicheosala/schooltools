from collections.abc import Callable, Sequence

import pytest
from httpx2 import Client, MockTransport, Request, Response

from schooltools.parsing import Classe
from schooltools.spaggiari import (
    URL_REGISTRO,
    Account,
    ErroreLogin,
    ErroreRegistro,
    Registro,
)

Gestore = Callable[[Request], Response]


def _registro(gestore: Gestore) -> Registro:
    return Registro(Client(transport=MockTransport(gestore), follow_redirects=True))


def _auth(**campi: object) -> dict[str, object]:
    return {"data": {"auth": {"errors": [], **campi}, "pfolio": False}}


def _dialogo(*account: tuple[str, str]) -> dict[str, object]:
    voci = "".join(
        f'<div class="item" x-account="{uid}">{nome}</div>' for uid, nome in account
    )
    return {
        "data": {
            "auth": {"verified": True, "loggedIn": False, "errors": []},
            "pfolio": {"filteredDialogHtml": f"<div>{voci}</div>"},
        }
    }


def test_login_riuscito() -> None:
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
        pytest.raises(ErroreLogin, match="Identificativo o password errati"),
    ):
        registro.login("prof", "sbagliata")


def test_login_con_piu_profili_usa_quello_scelto() -> None:
    inviati: list[bytes] = []

    def gestore(richiesta: Request) -> Response:
        if richiesta.method != "POST":
            return Response(200, html="<html></html>")
        inviati.append(richiesta.content)
        if richiesta.url.params.get("a") == "aLoginPwd":
            return Response(
                200, json=_dialogo(("uno", "Scuola A"), ("due", "Scuola B"))
            )
        return Response(200, json=_auth(verified=True, loggedIn=True))

    def scegli(account: Sequence[Account]) -> Account:
        assert [a.descrizione for a in account] == ["Scuola A", "Scuola B"]
        return account[1]

    with _registro(gestore) as registro:
        registro.login("prof", "segreta", scegli_account=scegli)

    assert b"uid=due" in inviati[1]


def test_login_predefinito_prende_il_primo_profilo() -> None:
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
    def gestore(richiesta: Request) -> Response:
        if richiesta.method == "POST":
            return Response(200, json=_auth(verified=True, loggedIn=False))
        return Response(200, html="<html></html>")

    with (
        _registro(gestore) as registro,
        pytest.raises(ErroreLogin, match="profilo"),
    ):
        registro.login("prof", "segreta")


def test_login_con_risposta_non_json() -> None:
    def gestore(richiesta: Request) -> Response:
        if richiesta.method == "POST":
            return Response(200, text="manutenzione in corso")
        return Response(200, html="<html></html>")

    with (
        _registro(gestore) as registro,
        pytest.raises(ErroreLogin, match="Risposta inattesa"),
    ):
        registro.login("prof", "segreta")


def test_login_con_errore_di_rete() -> None:
    with (
        _registro(lambda richiesta: Response(500)) as registro,
        pytest.raises(ErroreRegistro, match="Errore di rete"),
    ):
        registro.login("prof", "segreta")


def test_classi_dalla_pagina_di_selezione(selezione_html: str) -> None:
    with _registro(lambda richiesta: Response(200, html=selezione_html)) as registro:
        classi = registro.classi()

    assert classi == [Classe(id="111", nome="1E"), Classe(id="222", nome="3ELSA")]


def test_classi(registro_html: str) -> None:
    with _registro(lambda richiesta: Response(200, html=registro_html)) as registro:
        classi = registro.classi()

    assert len(classi) == 7
    assert classi[0].id == "2078364"


def test_classi_su_pagina_vuota() -> None:
    with (
        _registro(lambda richiesta: Response(200, html="<html></html>")) as registro,
        pytest.raises(ErroreRegistro, match="Nessuna classe"),
    ):
        registro.classi()


def test_studenti_chiede_la_classe_giusta(registro_html: str) -> None:
    richieste: list[Request] = []

    def gestore(richiesta: Request) -> Response:
        richieste.append(richiesta)
        return Response(200, html=registro_html)

    with _registro(gestore) as registro:
        studenti = registro.studenti(Classe(id="42", nome="1A"))

    assert richieste[0].url.params.get("classe_id") == "42"
    assert studenti == ["Rossi Giulio", "D'Agostino Maria Luisa", "Verdi Anna"]


def test_sessione_scaduta() -> None:
    def gestore(richiesta: Request) -> Response:
        if "regclasse" in richiesta.url.path:
            return Response(302, headers={"Location": "/home/app/default/login.php"})
        return Response(200, html="<html></html>")

    with (
        _registro(gestore) as registro,
        pytest.raises(ErroreRegistro, match="Sessione non valida"),
    ):
        registro.studenti(Classe(id="42", nome="1A"))


def test_url_registro_e_quello_del_cvv() -> None:
    assert URL_REGISTRO.endswith("/cvv/app/default/regclasse.php")
