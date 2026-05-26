# Gestione Edicola

Applicazione Web per la gestione di un'edicola virtuale: catalogo prodotti, vendita multi-prodotto, monitoraggio scorte e report delle entrate.

## Obiettivo

Fornire una Web App leggera per gestire il catalogo di prodotti (giornali, riviste, ecc.), registrare vendite multi-prodotto con aggiornamento immediato delle scorte e generare ricevute e report periodici delle entrate.

## Tecnologie

- **Linguaggio:** Python 3.14+
- **Web framework:** Flask
- **Database:** PostgreSQL
- **Frontend:** HTML/CSS (static), Bootstrap 5 (CDN), eventuale JS nelle pagine

## Requisiti funzionali

1. Gestione Prodotti
	- Aggiungere, modificare e rimuovere prodotti dall'inventario.
	- Ogni prodotto ha: codice univoco, nome, tipo, prezzo e quantità in magazzino.

2. Vendita Prodotti
	- Registrare la vendita di uno o più prodotti (carrello multi-prodotto).
	- Aggiornare la quantità a magazzino dopo la vendita.
	- Generare una ricevuta con data/ora, dettagli prodotti e totale.

3. Monitoraggio Inventario
	- Visualizzare l'elenco prodotti e filtrare per tipo.
	- Segnalare prodotti in esaurimento (quantità < soglia minima).

4. Report Entrate
	- Report per periodo (giornaliero/settimanale/mensile/annuale).
	- Totale vendite e riepilogo dei prodotti più venduti.

## Database e schema

Lo schema SQL è in [schema.sql](schema.sql). Le principali tabelle sono:

- `prodotti(id, codice, nome, tipo, prezzo, quantita, soglia_minima)` — tabella "master" del catalogo: ogni riga rappresenta un prodotto univoco (identificato dal `codice`) e tiene traccia dello stato attuale dell'inventario (`quantita`). Non registra quando un prodotto è stato venduto.
- `vendite(id, data_ora, totale)` — testata dello scontrino: ogni riga è un singolo atto di vendita (data/ora e totale). Non contiene il dettaglio dei prodotti venduti.
- `dettagli_vendita(id, vendita_id, prodotto_id, quantita, prezzo_unitario, subtotale)` — tabella ponte (many-to-many): memorizza le singole voci di uno scontrino (quante copie di quel prodotto sono state vendute, il `prezzo_unitario` al momento della vendita e il `subtotale`).

Dettagli e vincoli chiave:

- `dettagli_vendita` risolve la relazione molti-a-molti tra `prodotti` e `vendite`: una vendita può contenere più prodotti e lo stesso prodotto può comparire in più vendite.
- Il `prezzo_unitario` è intentionally denormalizzato in `dettagli_vendita` per preservare la storicità delle ricevute: se domani cambi il prezzo di un prodotto, le ricevute passate restano corrette.

Chiavi esterne:

- `dettagli_vendita.vendita_id → vendite.id` — dichiarata con `ON DELETE CASCADE`: se cancelli una vendita, le righe dei dettagli correlate vengono rimosse automaticamente (una riga dettaglio senza testata non ha senso).
- `dettagli_vendita.prodotto_id → prodotti.id` — dichiarata con `ON DELETE RESTRICT`: non è permesso cancellare un prodotto se è ancora citato in vendite storiche, per preservare l'integrità contabile.

Dettagli operativi:

- I prezzi e i calcoli monetari sono gestiti con `Decimal` e quantizzati a 2 decimali.
- La registrazione di una vendita avviene in una singola transazione che:
	- inserisce la testata in `vendite`,
	- inserisce le righe in `dettagli_vendita`,
	- aggiorna le scorte in `prodotti.quantita`,
	- calcola e aggiorna il `totale` della vendita.

## Installazione locale

1. Crea e attiva un virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Installa le dipendenze:

```bash
pip install -r requirements.txt
```

3. Crea il database PostgreSQL e applica lo schema:

```bash
# esempio con utente postgres locale
createdb edicola
psql -d edicola -f schema.sql
```

Oppure (se preferisci specificare host/utente):

```bash
psql -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER -d $DATABASE_NAME -f schema.sql
```

4. Configura il file `.env` (usa `python-dotenv`). Crea un file `.env` a partire da un esempio ([.env.example](edicola/.env.example)) e imposta le variabili seguenti:

```env
SECRET_KEY = your_secret_key_here
DATABASE_HOST = localhost
DATABASE_PORT = your_port_here
DATABASE_NAME = your_db_name_here
DATABASE_USER = your_db_user_here
DATABASE_PASSWORD = your_db_password_here
FLASK_DEBUG = 0/1
```

Generare una `SECRET_KEY` sicura (esempio):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

5. Avvia l'app in sviluppo:

```bash
source venv/bin/activate
python app.py
```

L'app sarà disponibile su http://localhost:5000

## Struttura del progetto

- [app.py](edicola/app.py) — entrypoint Flask; registra i blueprint e route principali.
- [config.py](edicola/config.py) — lettura variabili di ambiente e configurazioni.
- [db.py](edicola/db.py) — layer di accesso al database (query parametrizzate, transazioni).
- [schema.sql](schema.sql) — script per creare tabelle e indici.
- [requirements.txt](edicola/requirements.txt) — dipendenze Python.
- `routes/` — blueprint per le funzionalità (es. [routes/prodotti.py](edicola/routes/prodotti.py), [routes/vendite.py](edicola/routes/vendite.py), [routes/inventario.py](edicola/routes/inventario.py), [routes/report.py](edicola/routes/report.py)).
- `templates/` — template Jinja2 per le pagine.
- `static/` — file statici (CSS, JS, immagini).

## Note di sicurezza e produzione

- L'app in sviluppo usa `FLASK_DEBUG = 1` e non è pronta per l'uso in produzione.
- Impostare `FLASK_DEBUG = 0`, usare un server WSGI (es. Gunicorn) e proteggere le credenziali nel deployment.
- Valutare l'uso di CSRF protection (Flask-WTF) e connessioni sicure al DB (SSL) in produzione.