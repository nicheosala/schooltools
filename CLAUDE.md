# CLAUDE.md

Istruzioni per chi lavora su questo repository. Commenti, docstring e
documentazione sono in italiano senza lettere accentate (`e'`, `piu'`,
`cosi'`), come fa gia' il codice.

## Controlli di qualita'

- I controlli sono definiti una volta sola, in `.pre-commit-config.yaml`. La CI
  esegue `pre-commit run --all-files` e non una propria copia dei comandi, cosi'
  i due non possono divergere. Aggiungere un controllo significa aggiungere un
  hook li' e in nessun altro posto.
- La build non e' finita finche' questi non escono puliti, con zero errori e
  zero warning:

  ```bash
  uv run ruff check .
  uv run ruff format --check .
  uv run pyrefly check --min-severity warn
  uv run pytest
  ```

- `pytest` gira allo stage `pre-push` e non a ogni commit perche' e' troppo
  lento per un hook di commit; in CI ha un job dedicato. La soglia di copertura
  (`fail_under = 85`, con `branch = true`) sta in `[tool.coverage.report]` e non
  va abbassata per far passare la build.
- Annotazioni di tipo complete ovunque, suite di test compresa. Pyrefly gira con
  `preset = "strict"` su `src/` e `tests/`; `--min-severity warn` non e'
  opzionale, e' cio' che fa fallire la build su un warning. Le lacune negli stub
  di terze parti si colmano aggiungendo il pacchetto di stub alle dipendenze di
  sviluppo (come `types-openpyxl`), mai allentando la configurazione globale.
  Ogni soppressione superstite e' puntuale e accompagnata da una riga di
  commento che spiega perche'.
- Il `select` di ruff in `pyproject.toml` e' deliberatamente ampio: non
  restringerlo. Una nuova voce in `ignore` richiede un commento che giustifichi
  il conflitto.
- `tests/data/` e' un corpus byte-esatto. Nessun hook, formattatore o
  impostazione dell'editor puo' riscriverne fine riga, spazi finali o newline
  finale.
- Non allentare mai questi controlli per far passare il codice: si sistema il
  codice, oppure si ritaglia un'eccezione stretta e motivata.

## Invarianti

- **Le credenziali non entrano mai in un file committato.** Utente e password
  stanno in `schooltools.env`, che e' in `.gitignore`, o nelle variabili
  d'ambiente `SPAGGIARI_UTENTE` e `SPAGGIARI_PASSWORD`. L'unico file versionato
  che le nomina e' `schooltools.env.example`, che contiene solo segnaposto.
  Nessuna credenziale vera in una stringa del codice, in un test o in una
  fixture.
- **Nessun dato reale di studenti nel repository.** Il repo e' pubblico.
  `tests/data/` contiene pagine del registro ridotte e anonimizzate; le pagine
  scaricate davvero, che riportano nomi di persone reali, non si committano mai.
  Gli `*.xlsx` prodotti a runtime sono ignorati per lo stesso motivo.
- **I test non toccano la rete.** Il client `httpx2` e' sostituito da un
  `MockTransport` e le pagine arrivano dalle fixture su disco. La suite gira
  senza connessione e senza credenziali; un test che facesse una richiesta vera
  a `web.spaggiari.eu` e' da rifiutare.
- **`parsing.py` resta puro.** Prende HTML e restituisce dati: niente rete,
  niente filesystem, niente `print`. E' cio' che lo rende testabile con le
  fixture. Tutto l'I/O di rete sta in `spaggiari.py`, la scrittura in
  `export.py`.
- **Il parsing non puo' dare per scontato l'HTML del registro.** ClasseViva
  cambia markup senza preavviso: ogni estrazione va difesa (`isinstance(...,
  Tag)`, attributi che possono mancare, liste vuote) e un elemento assente
  diventa un valore vuoto o un `RegistroError`, mai un `AttributeError` o un
  `KeyError` che risale all'utente. I layout alternativi gia' gestiti - menu a
  tendina, pagina di selezione, docente con una classe sola - vanno tenuti
  tutti: sono pagine diverse che il registro serve davvero.
- **Le dipendenze di runtime sono tre: `beautifulsoup4`, `httpx2`,
  `openpyxl`.** Tutto il resto sta in `dependency-groups.dev`. In particolare
  niente libreria di configurazione: `leggi_env` fa apposta il minimo che serve
  a leggere un `.env`.
- **La CLI non fa risalire traceback all'utente.** Errori di credenziali, di
  rete, di scrittura e l'interruzione da tastiera (`Ctrl-C`, EOF) diventano un
  messaggio su una riga sola e uscita 1. Chiudere con `Ctrl-C` un'interfaccia
  che fa domande e' un modo normale di rispondere, non un guasto.
- **`students.write_to_csv` non e' codice morto.** Non ha chiamanti nel
  repository, ma e' esportata in `__all__` ed e' l'export CSV per
  l'importazione utenti di Microsoft 365: non va rimossa come funzione
  inutilizzata.
