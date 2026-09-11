"""Estrazione dei dati dalle pagine HTML del registro elettronico ClasseViva.

Le funzioni di questo modulo sono pure: prendono in ingresso l'HTML di una
pagina e restituiscono dati. Non toccano la rete, cosi' da poter essere
testate con delle fixture salvate su disco.
"""

from dataclasses import dataclass
from re import sub
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup, Tag

LUNGHEZZA_SIGLA = 4
SELETTORE_MENU = "#lista_classi a[href]"
SELETTORE_SELEZIONE = "a[href*='regclasse.php'][href*='classe_id='][title]"
SELETTORE_ACCOUNT = "[x-account]"


@dataclass(frozen=True, slots=True)
class Classe:
    """Una classe del registro, con l'identificativo usato da ClasseViva."""

    id: str
    nome: str


@dataclass(frozen=True, slots=True)
class Account:
    """Uno dei profili tra cui scegliere quando un'utenza ne ha piu' di uno."""

    uid: str
    descrizione: str


def parse_studenti(html: str) -> list[str]:
    """I nomi degli studenti elencati nel registro di classe."""
    soup = _minestra(html)
    studenti: list[str] = []
    for cella in soup.select("td.elenco_studenti"):
        nome = cella.find("div")
        if isinstance(nome, Tag):
            studenti.append(_testo(nome).title())
    return studenti


def parse_nome_classe(html: str) -> str | None:
    """Il nome abbreviato della classe a cui si riferisce la pagina."""
    soup = _minestra(html)
    intestazione = soup.find(id="classe_change")
    if isinstance(intestazione, Tag):
        return abbrevia(_testo(intestazione)) or None
    return None


def parse_classi(html: str) -> list[Classe]:
    """L'elenco delle classi del docente.

    Funziona sia sulla pagina di selezione della classe (`gioprof_selezione`),
    dove ogni classe e' un riquadro col suo codice, sia sul menu a tendina del
    registro di classe. Se non c'e' nessuno dei due (docente con una sola
    classe) si ripiega sulla classe della pagina stessa.
    """
    soup = _minestra(html)

    for selettore in (SELETTORE_MENU, SELETTORE_SELEZIONE):
        classi = _classi_dai_collegamenti(soup, selettore)
        if classi:
            return classi

    nome = parse_nome_classe(html)
    if nome is None:
        return []
    for a in soup.select("a[href*='regclasse.php']"):
        href = a.get("href")
        if isinstance(href, str):
            id_classe = _classe_id(href)
            if id_classe:
                return [Classe(id=id_classe, nome=nome)]
    return []


def parse_account(html: str) -> list[Account]:
    """I profili proposti quando un'utenza e' collegata a piu' scuole.

    L'HTML e' il frammento di dialogo che il server di autenticazione
    restituisce dentro la risposta JSON del login.
    """
    account: list[Account] = []
    for voce in _minestra(html).select(SELETTORE_ACCOUNT):
        uid = voce.get("x-account")
        if isinstance(uid, str) and uid:
            account.append(Account(uid=uid, descrizione=_testo(voce) or uid))
    return account


def abbrevia(nome: str) -> str:
    """Il solo codice della classe: "1E LSA LICEO SCIENTIFICO..." -> "1E LSA".

    Il codice e' fatto dalla prima parola (quella con il numero dell'anno) e
    dalle sigle brevi che la seguono; il resto e' la descrizione del corso, che
    e' uguale per tutte le classi e non serve a distinguerle. Se il nome non
    comincia con un numero viene restituito invariato.
    """
    parti = nome.split()
    if not _comincia_con_anno(parti):
        return nome

    codice = [parti[0]]
    for parte in parti[1:]:
        if parte.isalpha() and parte.isupper() and len(parte) <= LUNGHEZZA_SIGLA:
            codice.append(parte)
        else:
            break
    return " ".join(codice)


def sigla_classe(nome: str) -> str:
    """La sigla della classe tutta attaccata: "1A LL LICEO LINGUISTICO..." -> "1ALL".

    E' `abbrevia` senza gli spazi interni, la forma compatta che serve dove la
    classe fa da etichetta e deve venire sempre uguale, comunque sia scritta
    nella pagina o nel file di partenza ("1E LSA" e "1ELSA" danno lo stesso
    risultato). Un nome che non comincia con l'anno di corso non e' il codice di
    una classe: torna com'e', con i soli spazi di troppo ripuliti.

    Args:
        nome: Nome della classe, per esteso o gia' abbreviato.

    Returns:
        La sigla, oppure il nome ripulito se non c'e' una sigla da isolare.
    """
    if not _comincia_con_anno(nome.split()):
        return " ".join(nome.split())
    return "".join(abbrevia(nome).split())


def dividi_nome(studente: str) -> tuple[str, str]:
    """Divide "COGNOME Nome Secondo" in ("COGNOME", "Nome Secondo").

    E' la forma in cui il registro scrive i nomi, quella che restituisce
    `parse_studenti`: il cognome e' la prima parola, il nome tutto il resto.
    """
    parti = studente.split()
    if not parti:
        return "", ""
    return parti[0], " ".join(parti[1:])


def _minestra(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _testo(tag: Tag) -> str:
    return sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()


def _classe_id(href: str) -> str | None:
    valori = parse_qs(urlsplit(href).query).get("classe_id", [])
    return valori[0] if valori and valori[0] else None


def _classi_dai_collegamenti(soup: BeautifulSoup, selettore: str) -> list[Classe]:
    classi: dict[str, Classe] = {}
    for a in soup.select(selettore):
        href = a.get("href")
        if not isinstance(href, str):
            continue
        id_classe = _classe_id(href)
        nome = abbrevia(_testo(a))
        if id_classe and nome and id_classe not in classi:
            classi[id_classe] = Classe(id=id_classe, nome=nome)
    return list(classi.values())


def _comincia_con_anno(parti: list[str]) -> bool:
    """Se la prima parola porta il numero dell'anno, il nome e' un codice di classe."""
    return bool(parti) and any(c.isdigit() for c in parti[0])
