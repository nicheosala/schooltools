# Schooltools

Scarica dal registro elettronico ClasseViva (Spaggiari) i nomi degli studenti
delle tue classi e li mostra a schermo o li salva in un file xlsx, con un
foglio per classe.

## Requisiti

- Python 3.14 o superiore
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- un account docente ClasseViva

## Installazione

```sh
git clone http://localhost:3000/nicheosala/schooltools.git
cd schooltools
uv sync
```

`uv sync` crea l'ambiente virtuale in `.venv` e installa le dipendenze
elencate in `pyproject.toml`; non serve attivarlo a mano, ci pensa `uv run`.

## Configurazione

Copia il file di esempio e mettici le credenziali con cui accedi a Spaggiari:

```sh
cp credenziali.env.esempio credenziali.env
```

```
SPAGGIARI_UTENTE=il-tuo-codice-personale
SPAGGIARI_PASSWORD=la-tua-password
```

`credenziali.env` è ignorato da git, quindi non finisce nei commit. In
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
| `--env FILE` | file con le credenziali (predefinito `credenziali.env`) |
| `--help` | l'elenco completo delle opzioni |

`--file` serve quando non c'è connessione o il registro è irraggiungibile:
salva la pagina del registro di classe dal browser e passala al programma.

## Sviluppo

```sh
uv run pytest                                    # 61 test, nessuna rete
uv run ruff check . && uv run ruff format .      # stile
uv run ty check                                  # tipi
```

I test non toccano la rete: le pagine di ClasseViva sono salvate ridotte e
anonimizzate in `tests/data/`, e il client HTTP viene sostituito da un
`MockTransport`.

## Struttura

| File | Contenuto |
| --- | --- |
| `schooltools/cli.py` | domande interattive e opzioni da riga di comando |
| `schooltools/spaggiari.py` | login e lettura delle pagine del registro |
| `schooltools/parsing.py` | estrazione di classi e studenti dall'HTML (funzioni pure) |
| `schooltools/export.py` | scrittura del file xlsx |
| `schooltools/config.py` | lettura di `credenziali.env` |
| `schooltools/students.py` | gruppi, estrazioni a sorte, export csv per Microsoft 365 |

Il login riproduce quello che fa il browser: una POST su
`auth-p7/app/default/AuthApi4.php` e poi le pagine del registro riusando il
cookie di sessione. Se l'utenza è collegata a più profili, il programma chiede
quale usare.
