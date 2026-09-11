# Schooltools

Scarica dal registro elettronico ClasseViva (Spaggiari) i nomi degli studenti
delle tue classi e li mostra a schermo o li salva in un file xlsx, con un
foglio per classe.

## Requisiti

- Python 3.14 (la versione è fissata in `.python-version`; se manca,
  `uv` la scarica da solo)
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- un account docente ClasseViva

## Installazione

```sh
git clone https://github.com/nicheosala/schooltools.git
cd schooltools
uv sync
```

`uv sync` crea l'ambiente virtuale in `.venv` e installa le dipendenze
elencate in `pyproject.toml`; non serve attivarlo a mano, ci pensa `uv run`.

Se hai intenzione di modificare il codice, installa anche gli hook di
pre-commit: al momento del commit sistemano stile e formattazione e
controllano i tipi, mentre al momento del push eseguono anche i test.

```sh
uv run pre-commit install
```

## Configurazione

Copia il file di esempio e mettici le credenziali con cui accedi a Spaggiari:

```sh
cp schooltools.env.example schooltools.env
```

```
SPAGGIARI_UTENTE=il-tuo-codice-personale
SPAGGIARI_PASSWORD=la-tua-password
```

`schooltools.env` è ignorato da git, quindi non finisce nei commit. In
alternativa si possono usare le variabili d'ambiente con lo stesso nome, utile
se preferisci tenere la password in un gestore di segreti:

```sh
SPAGGIARI_UTENTE=... SPAGGIARI_PASSWORD=... uv run python -m schooltools
```

## Uso

```sh
uv run python -m schooltools
```

Il programma fa il login e poi ti fa due domande:

```
Per quale classe vuoi ottenere i nomi degli studenti?
  1) tutte
  2) 1E
  3) 2E
  ...
Scelta [1]:

Cosa vuoi fare con i nomi?
  1) mostrali a schermo
  2) scrivili in un file xlsx
Scelta [1]:
```

Scegliendo il file xlsx ottieni un foglio per ogni classe, chiamato con il
codice della classe (`1E`, `3ELSA`, `4F`), con le colonne `Cognome` e `Nome`.

Ogni domanda si può saltare passando l'opzione corrispondente:

```sh
uv run python -m schooltools --classe 1E --schermo
uv run python -m schooltools --classe tutte --xlsx studenti.xlsx
```

| Opzione | Significato |
| --- | --- |
| `--classe NOME` | nome anche parziale della classe, oppure `tutte` |
| `--xlsx [FILE]` | scrivi in un file xlsx (predefinito `studenti.xlsx`) |
| `--schermo` | mostra i nomi a schermo |
| `--file HTML` | leggi da una pagina `regclasse.php` salvata invece che dalla rete |
| `--env FILE` | file con le credenziali (predefinito `schooltools.env`) |
| `--help` | l'elenco completo delle opzioni |

`--file` serve quando non c'è connessione o il registro è irraggiungibile:
salva la pagina del registro di classe dal browser e passala al programma.

### Preparare l'importazione degli utenti (`teams`)

Il sotto-comando `teams` non tocca il registro: prende un elenco che hai già —
tipicamente quello della segreteria, con le colonne `Nome`, `Cognome` e
`Classe` — e ne scrive un altro nel formato che il portale Microsoft 365 si
aspetta per l'importazione degli utenti, quella da cui poi nascono i team delle
classi.

```sh
uv run python -m schooltools teams --from segreteria.xlsx --to utenti.xlsx
```

| Opzione | Significato |
| --- | --- |
| `--from FILE` | elenco xlsx di partenza, con le colonne `Nome`, `Cognome`, `Classe` |
| `--to FILE` | file xlsx da scrivere, sovrascritto se esiste |

Ogni studente diventa una riga con l'indirizzo `nome.cognome@dominio`, la
posizione `Studente` e la classe nel campo `Reparto`, che è quello su cui
l'importazione raggruppa gli utenti. Gli elenchi della segreteria arrivano di
solito in maiuscolo e con il nome del corso per esteso: nomi e cognomi tornano
con le sole iniziali maiuscole e la classe si riduce alla sua sigla.

Una riga del file di partenza:

| Nome | Cognome | Classe |
| --- | --- | --- |
| GIULIO | ROSSI | 1A LL LICEO LINGUISTICO NUOVO ORDINAMENTO |

diventa una riga del file prodotto:

| Nome utente | Nome | Cognome | Nome visualizzato | Posizione | Reparto |
| --- | --- | --- | --- | --- | --- |
| `giulio.rossi@…` | Giulio | Rossi | Giulio Rossi | Studente | 1ALL |

Le parole che hanno già delle minuscole non vengono toccate, così `de Luca` e
`McDonald` restano come li ha scritti chi ha compilato l'elenco.

Del file di partenza non si dà per scontato il tracciato: l'intestazione può
non essere sulla prima riga, le colonne possono stare in un ordine qualunque e
le righe vuote vengono saltate. Se manca una colonna o una riga piena non ha né
nome né cognome, il programma lo dice in una riga sola e esce con codice 1.

## Sviluppo

| Comando | Cosa fa |
| --- | --- |
| `uv sync` | installa le dipendenze nell'ambiente virtuale |
| `uv run pytest` | esegue i test e stampa la copertura |
| `uv run ruff check .` | lint |
| `uv run ruff format .` | formattazione |
| `uv run pyrefly check --min-severity warn` | controllo dei tipi |
| `uv audit --preview-features audit-command` | vulnerabilità note nelle dipendenze |
| `uv build` | costruisce sdist e wheel in `dist/` |
| `uv run pre-commit run --all-files` | gli hook del commit su tutto il repo |
| `uv run pre-commit run --all-files --hook-stage pre-push` | come sopra, più i test |

Gli stessi controlli girano su GitHub Actions a ogni push e pull request
(`.github/workflows/ci.yml`), con `uv sync --locked`, che fallisce se
`uv.lock` non è allineato a `pyproject.toml`. La CI non riscrive i comandi:
esegue `pre-commit run --all-files`, così gli hook locali e i controlli
remoti non possono divergere. Test e scansione delle dipendenze hanno un job
a sé; quest'ultimo gira anche una volta a settimana, perché una vulnerabilità
può essere pubblicata senza che il lock file cambi.

I test non toccano la rete: le pagine di ClasseViva sono salvate ridotte e
anonimizzate in `tests/data/`, e il client HTTP viene sostituito da un
`MockTransport`.

## Struttura

| File | Contenuto |
| --- | --- |
| `src/schooltools/cli.py` | domande interattive e opzioni da riga di comando |
| `src/schooltools/spaggiari.py` | login e lettura delle pagine del registro |
| `src/schooltools/parsing.py` | estrazione di classi e studenti dall'HTML (funzioni pure) |
| `src/schooltools/export.py` | scrittura del file xlsx |
| `src/schooltools/config.py` | lettura di `schooltools.env` |
| `src/schooltools/students.py` | tracciato di importazione utenti di Microsoft 365 |
| `src/schooltools/teams.py` | lettura dell'elenco `Nome`/`Cognome`/`Classe` di partenza |

Il login riproduce quello che fa il browser: una POST su
`auth-p7/app/default/AuthApi4.php` e poi le pagine del registro riusando il
cookie di sessione. Se l'utenza è collegata a più profili, il programma chiede
quale usare.

## Licenza

Questo progetto è rilasciato sotto [CC0 1.0
Universal](https://creativecommons.org/publicdomain/zero/1.0/): l'autore
rinuncia a ogni diritto d'autore, quindi puoi copiarlo, modificarlo e
distribuirlo per qualsiasi scopo, anche commerciale, senza chiedere permesso e
senza obbligo di attribuzione. Il testo completo è nel file `LICENSE`.
