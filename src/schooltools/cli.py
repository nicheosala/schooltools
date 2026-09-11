"""Interfaccia interattiva per ottenere i nomi degli studenti dal registro."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from schooltools.config import (
    PERCORSO_PREDEFINITO,
    CredenzialiMancantiError,
    carica_credenziali,
)
from schooltools.export import scrivi_utenti_xlsx, scrivi_xlsx
from schooltools.parsing import Classe, parse_nome_classe, parse_studenti
from schooltools.spaggiari import Account, Registro, RegistroError
from schooltools.teams import COLONNE_ORIGINE, leggi_origine

if TYPE_CHECKING:
    from argparse import _SubParsersAction
    from collections.abc import Sequence

TUTTE = "tutte"
XLSX_PREDEFINITO = Path("studenti.xlsx")
TEAMS = "teams"


def argomenti(argv: Sequence[str] | None = None) -> Namespace:
    """Interpreta gli argomenti della riga di comando.

    Args:
        argv: Argomenti da interpretare; `None` per quelli di `sys.argv`.

    Returns:
        Le opzioni riconosciute.
    """
    parser = ArgumentParser(
        prog="schooltools",
        description=(
            "Scarica dal registro elettronico Spaggiari i nomi degli studenti "
            "di una classe (o di tutte) e li mostra a schermo o li scrive in "
            "un file xlsx, un foglio per classe."
        ),
    )
    parser.add_argument(
        "--classe",
        help=f"nome (anche parziale) della classe, oppure '{TUTTE}'",
    )
    parser.add_argument(
        "--xlsx",
        type=Path,
        nargs="?",
        const=XLSX_PREDEFINITO,
        help=f"scrivi i nomi in questo file xlsx (predefinito: {XLSX_PREDEFINITO})",
    )
    parser.add_argument(
        "--schermo",
        action="store_true",
        help="mostra i nomi a schermo invece di scriverli in un file",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="leggi da una pagina HTML salvata invece che dalla rete",
    )
    parser.add_argument(
        "--env",
        type=Path,
        default=PERCORSO_PREDEFINITO,
        help=f"file con le credenziali (predefinito: {PERCORSO_PREDEFINITO})",
    )
    _aggiungi_teams(parser.add_subparsers(dest="comando", metavar="COMANDO"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Esegue il programma e traduce ogni guasto previsto in un codice di uscita.

    Gli errori di credenziali, di rete e di scrittura non risalgono all'utente
    come traceback: diventano un messaggio su una riga sola. Anche l'interruzione
    da tastiera e' trattata cosi', perche' l'interfaccia fa domande e chiuderla
    con Ctrl-C e' un modo normale di rispondere.

    Args:
        argv: Argomenti da interpretare; `None` per quelli di `sys.argv`.

    Returns:
        0 se il lavoro e' andato a buon fine, 1 altrimenti.
    """
    args = argomenti(argv)
    try:
        if args.comando == TEAMS:
            _teams(args)
        else:
            _consegna(_raccogli(args), args)
    except (CredenzialiMancantiError, RegistroError, ValueError, OSError) as errore:
        print(f"Errore: {errore}")
        return 1
    except EOFError, KeyboardInterrupt:
        print("\nAnnullato.")
        return 1
    return 0


def _aggiungi_teams(comandi: _SubParsersAction[ArgumentParser]) -> None:
    """Aggiunge il sotto-comando `teams`, che non tocca il registro."""
    colonne = ", ".join(f"`{c}`" for c in COLONNE_ORIGINE)
    teams = comandi.add_parser(
        TEAMS,
        help="converti un elenco di studenti nel formato di importazione utenti",
        description=(
            f"Legge un file xlsx con le colonne {colonne} e ne scrive un altro "
            "nel formato che il portale Microsoft 365 si aspetta per "
            "l'importazione degli utenti, una riga per studente. Le righe "
            "vuote del file di origine vengono saltate."
        ),
    )
    teams.add_argument(
        "--from",
        dest="origine",
        type=Path,
        required=True,
        metavar="FILE",
        help=f"file xlsx di origine, con le colonne {colonne}",
    )
    teams.add_argument(
        "--to",
        dest="destinazione",
        type=Path,
        required=True,
        metavar="FILE",
        help="file xlsx da scrivere, sovrascritto se esiste",
    )


def _teams(args: Namespace) -> None:
    """Converte l'elenco di origine nel formato di importazione utenti."""
    studenti = leggi_origine(args.origine)
    percorso = scrivi_utenti_xlsx(args.destinazione, studenti)
    verbo, quanti = (
        ("Scritto", "1 studente")
        if len(studenti) == 1
        else ("Scritti", f"{len(studenti)} studenti")
    )
    print(f"{verbo} {quanti} in {percorso}.")


def _raccogli(args: Namespace) -> dict[str, list[str]]:
    """Gli studenti richiesti, per classe."""
    if args.file is not None:
        html = Path(args.file).read_text(encoding="utf-8")
        nome = parse_nome_classe(html) or "Classe"
        return {nome: parse_studenti(html)}

    credenziali = carica_credenziali(args.env)
    with Registro.apri() as registro:
        print("Accesso al registro in corso...")
        registro.login(credenziali.utente, credenziali.password, scegli_account=_scegli_account)
        classi = registro.classi()
        scelte = _scegli_classi(classi, args.classe)
        return {classe.nome: registro.studenti(classe) for classe in scelte}


def _consegna(elenchi: dict[str, list[str]], args: Namespace) -> None:
    if args.xlsx is not None:
        percorso = scrivi_xlsx(Path(args.xlsx), elenchi)
    elif args.schermo or not _vuole_xlsx():
        _mostra(elenchi)
        return
    else:
        percorso = scrivi_xlsx(_chiedi_percorso(), elenchi)

    fogli = len(elenchi)
    studenti = sum(len(s) for s in elenchi.values())
    quanti = "1 foglio" if fogli == 1 else f"{fogli} fogli"
    print(f"Scritti {studenti} studenti in {percorso} ({quanti}).")


def _mostra(elenchi: dict[str, list[str]]) -> None:
    for nome, studenti in elenchi.items():
        print(f"\n{nome}")
        if not studenti:
            print("  (nessuno studente)")
        for i, studente in enumerate(studenti, 1):
            print(f"  {i:2d}. {studente}")


def _scegli_classi(classi: Sequence[Classe], richiesta: str | None) -> list[Classe]:
    if richiesta is not None:
        if richiesta.strip().lower() == TUTTE:
            return list(classi)
        cercata = richiesta.strip().lower()
        trovate = [c for c in classi if cercata in c.nome.lower()]
        if not trovate:
            raise ValueError(f"Nessuna classe corrisponde a {richiesta!r}")
        return trovate

    voci = [TUTTE, *(c.nome for c in classi)]
    scelta = _chiedi_voce("Per quale classe vuoi ottenere i nomi degli studenti?", voci)
    return list(classi) if scelta == 0 else [classi[scelta - 1]]


def _scegli_account(account: Sequence[Account]) -> Account:
    if len(account) == 1:
        return account[0]
    scelta = _chiedi_voce("Con quale profilo vuoi accedere?", [a.descrizione for a in account])
    return account[scelta]


def _vuole_xlsx() -> bool:
    return (
        _chiedi_voce(
            "Cosa vuoi fare con i nomi?",
            ["mostrali a schermo", "scrivili in un file xlsx"],
        )
        == 1
    )


def _chiedi_percorso() -> Path:
    risposta = input(f"Nome del file [{XLSX_PREDEFINITO}]: ").strip()
    return Path(risposta) if risposta else XLSX_PREDEFINITO


def _chiedi_voce(domanda: str, voci: Sequence[str]) -> int:
    """Mostra un elenco numerato e restituisce l'indice della voce scelta."""
    print(f"\n{domanda}")
    for i, voce in enumerate(voci, 1):
        print(f"  {i}) {voce}")

    while True:
        risposta = input("Scelta [1]: ").strip() or "1"
        if risposta.isdigit() and 1 <= int(risposta) <= len(voci):
            return int(risposta) - 1
        print(f"Inserisci un numero da 1 a {len(voci)}.")
