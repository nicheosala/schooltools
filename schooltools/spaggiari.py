"""Accesso automatico al registro elettronico ClasseViva di Spaggiari.

Riproduce quello che fa il browser: autenticazione su `AuthApi4.php` e poi
lettura delle pagine del registro di classe riusando i cookie di sessione.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from json import JSONDecodeError
from types import TracebackType
from typing import Any, Self

from bs4 import BeautifulSoup, Tag
from httpx2 import Client, HTTPError, Response

from schooltools.parsing import Classe, parse_classi, parse_studenti

BASE = "https://web.spaggiari.eu"
URL_PAGINA_LOGIN = f"{BASE}/home/app/default/login.php"
URL_API_AUTH = f"{BASE}/auth-p7/app/default/AuthApi4.php"
URL_REGISTRO = f"{BASE}/cvv/app/default/regclasse.php"

DESTINAZIONE = "cvv"
AGENTE = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)


class ErroreRegistro(Exception):
    """Qualcosa e' andato storto parlando con il registro elettronico."""


class ErroreLogin(ErroreRegistro):
    """L'autenticazione non e' andata a buon fine."""


@dataclass(frozen=True, slots=True)
class Account:
    """Uno dei profili tra cui scegliere quando un'utenza ne ha piu' di uno."""

    uid: str
    descrizione: str


SceltaAccount = Callable[[Sequence[Account]], Account]


def _primo_account(account: Sequence[Account]) -> Account:
    return account[0]


def _json(risposta: Response) -> dict[str, Any]:
    try:
        dati = risposta.json()
    except (JSONDecodeError, ValueError) as errore:
        raise ErroreLogin(
            "Risposta inattesa dal server di autenticazione di Spaggiari"
        ) from errore
    if not isinstance(dati, dict):
        raise ErroreLogin("Risposta inattesa dal server di autenticazione di Spaggiari")
    return dati


def _auth(dati: dict[str, Any]) -> dict[str, Any]:
    corpo = dati.get("data")
    auth = corpo.get("auth") if isinstance(corpo, dict) else None
    return auth if isinstance(auth, dict) else {}


def _errori(auth: dict[str, Any]) -> str:
    errori = auth.get("errors")
    if isinstance(errori, list) and errori:
        return "; ".join(str(e) for e in errori)
    return "credenziali rifiutate dal registro"


def _account(dati: dict[str, Any]) -> list[Account]:
    corpo = dati.get("data")
    pfolio = corpo.get("pfolio") if isinstance(corpo, dict) else None
    if not isinstance(pfolio, dict):
        return []

    html = pfolio.get("filteredDialogHtml") or pfolio.get("fullDialogHtml")
    if not isinstance(html, str):
        return []

    account: list[Account] = []
    soup = BeautifulSoup(html, "html.parser")
    for voce in soup.select("[x-account]"):
        if not isinstance(voce, Tag):
            continue
        uid = voce.get("x-account")
        if isinstance(uid, str) and uid:
            descrizione = " ".join(voce.get_text(" ", strip=True).split())
            account.append(Account(uid=uid, descrizione=descrizione or uid))
    return account


class Registro:
    """Una sessione autenticata sul registro elettronico."""

    def __init__(self, client: Client) -> None:
        self._client = client

    @classmethod
    def apri(cls, timeout: float = 30.0) -> Self:
        return cls(
            Client(
                headers={"User-Agent": AGENTE},
                follow_redirects=True,
                timeout=timeout,
            )
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        valore: BaseException | None,
        traccia: TracebackType | None,
    ) -> None:
        self.chiudi()

    def chiudi(self) -> None:
        self._client.close()

    def login(
        self,
        utente: str,
        password: str,
        scegli_account: SceltaAccount = _primo_account,
    ) -> None:
        """Autentica la sessione con le credenziali di Spaggiari.

        Se l'utenza e' collegata a piu' profili, `scegli_account` decide quale
        usare; di default viene preso il primo.
        """

        self._get(URL_PAGINA_LOGIN)
        dati = _json(
            self._post(
                URL_API_AUTH,
                {"a": "aLoginPwd"},
                {
                    "cid": "",
                    "uid": utente,
                    "pwd": password,
                    "pin": "",
                    "target": DESTINAZIONE,
                },
            )
        )
        auth = _auth(dati)

        if not auth.get("verified"):
            raise ErroreLogin(f"Accesso non riuscito: {_errori(auth)}")

        if not auth.get("loggedIn"):
            account = _account(dati)
            if not account:
                raise ErroreLogin(
                    "Accesso non riuscito: il registro chiede di scegliere un "
                    "profilo ma non ne ha proposto nessuno"
                )
            scelto = scegli_account(account)
            dati = _json(
                self._post(URL_API_AUTH, {"a": "aLoginSam"}, {"uid": scelto.uid})
            )
            auth = _auth(dati)
            if not auth.get("loggedIn"):
                raise ErroreLogin(f"Accesso non riuscito: {_errori(auth)}")

    def classi(self) -> list[Classe]:
        """Le classi visibili nel registro.

        Senza `classe_id` il registro rimanda alla pagina di selezione della
        classe, da cui si ricavano codici e identificativi.
        """

        classi = parse_classi(self._pagina_registro(None))
        if not classi:
            raise ErroreRegistro(
                "Nessuna classe trovata nel registro: la sessione potrebbe "
                "essere scaduta"
            )
        return classi

    def studenti(self, classe: Classe) -> list[str]:
        """I nomi degli studenti della classe indicata."""

        return parse_studenti(self._pagina_registro(classe.id))

    def _pagina_registro(self, id_classe: str | None) -> str:
        parametri = {"classe_id": id_classe, "gruppo_id": ""} if id_classe else None
        risposta = self._get(URL_REGISTRO, parametri)
        if "login.php" in str(risposta.url):
            raise ErroreRegistro("Sessione non valida: e' necessario rifare il login")
        return risposta.text

    def _get(self, url: str, parametri: dict[str, str] | None = None) -> Response:
        try:
            risposta = self._client.get(url, params=parametri)
            risposta.raise_for_status()
        except HTTPError as errore:
            raise ErroreRegistro(f"Errore di rete su {url}: {errore}") from errore
        return risposta

    def _post(
        self, url: str, parametri: dict[str, str], dati: dict[str, str]
    ) -> Response:
        try:
            risposta = self._client.post(
                url,
                params=parametri,
                data=dati,
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            risposta.raise_for_status()
        except HTTPError as errore:
            raise ErroreRegistro(f"Errore di rete su {url}: {errore}") from errore
        return risposta
