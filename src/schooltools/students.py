"""Il tracciato di importazione utenti di Microsoft 365.

E' qui che uno studente prende la forma con cui si vedra' nel portale: le
colonne che il portale si aspetta, l'indirizzo di posta, le iniziali maiuscole
e la sigla della classe. Sono funzioni pure: chi legge i dati e' `teams.py`,
chi li scrive `export.py`.
"""

from typing import NamedTuple

from schooltools.parsing import sigla_classe

CAMPI_UTENTI = [
    "Nome utente",
    "Nome",
    "Cognome",
    "Nome visualizzato",
    "Posizione",
    "Reparto",
    "Numero ufficio",
    "Telefono ufficio",
    "Cellulare",
    "Fax",
    "Indirizzo di posta elettronica alternativo",
    "Indirizzo",
    "Città",
    "Stato o provincia",
    "CAP",
    "Paese o area geografica",
]

DOMINIO = "istitutobachelet.edu.it"

POSIZIONE = "Studente"


class Studente(NamedTuple):
    """Uno studente nella forma che serve all'importazione utenti.

    Attributes:
        nome: Nome di battesimo, anche composto ("Maria Luisa").
        cognome: Cognome, anche composto ("De Luca").
        classe: Classe di appartenenza; vuota quando non si sa.
    """

    nome: str
    cognome: str
    classe: str = ""


def riga_utente(studente: Studente) -> list[str]:
    """Compone la riga di importazione utenti di Microsoft 365 per uno studente.

    Le colonne e il loro ordine sono quelli di `CAMPI_UTENTI`, cioe' quelli che il
    portale si aspetta: allo studente tocca un indirizzo `nome.cognome@DOMINIO`,
    la posizione "Studente" e la classe come reparto, cosi' che l'importazione
    possa raggruppare per classe. I campi rimanenti restano vuoti.

    E' qui che i dati prendono la forma con cui si vedranno nel portale: nome e
    cognome con le sole iniziali maiuscole (`capitalizza`) e la classe ridotta
    alla sua sigla (`sigla_classe`), perche' come reparto serve un'etichetta
    breve e sempre uguale, non la descrizione per esteso del corso.

    Args:
        studente: Studente da descrivere.

    Returns:
        Una riga lunga quanto `CAMPI_UTENTI`.
    """
    nome = capitalizza(studente.nome)
    cognome = capitalizza(studente.cognome)
    return [
        indirizzo(nome, cognome),
        nome,
        cognome,
        f"{nome} {cognome}".strip(),
        POSIZIONE,
        sigla_classe(studente.classe),
        *[""] * (len(CAMPI_UTENTI) - 6),
    ]


def indirizzo(nome: str, cognome: str) -> str:
    """Costruisce l'indirizzo `nome.cognome@DOMINIO` di uno studente.

    Args:
        nome: Nome di battesimo.
        cognome: Cognome.

    Returns:
        L'indirizzo di posta, senza maiuscole, apostrofi, punti ne' spazi.
    """
    return f"{sanitize(nome)}.{sanitize(cognome)}@{DOMINIO}"


def capitalizza(nome: str) -> str:
    """Riporta alle sole iniziali maiuscole un nome scritto tutto in maiuscolo.

    Gli elenchi della segreteria arrivano in maiuscolo ("ROSSI GIULIO"), che nel
    portale si legge male: "Rossi Giulio" e' la forma giusta. Le parole che
    hanno gia' delle minuscole si lasciano stare, perche' chi le ha scritte
    cosi' aveva verosimilmente le sue ragioni ("de Luca", "McDonald").

    Args:
        nome: Nome, cognome o parte di essi.

    Returns:
        Il nome con l'iniziale maiuscola di ogni parola, spazi di troppo esclusi.
    """
    return " ".join(
        parola if any(c.islower() for c in parola) else parola.title() for parola in nome.split()
    )


def sanitize(s: str) -> str:
    """Riduce una parte di nome alla forma ammessa in un indirizzo di posta.

    Args:
        s: Nome o cognome da ripulire.

    Returns:
        Il testo in minuscolo, senza apostrofi, punti ne' spazi.
    """
    return s.lower().replace("'", "").replace(".", "").replace(" ", "")
