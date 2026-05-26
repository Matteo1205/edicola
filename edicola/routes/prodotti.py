import db
import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.utils import parse_int, parse_float


# blueprint per la gestione dei prodotti
bp = Blueprint('prodotti', __name__, url_prefix='/prodotti')


# rotta per visualizzare la lista dei prodotti, con filtro per tipo
@bp.route('/')
def lista():
    # otteniamo il filtro 
    tipo_filter = request.args.get('tipo', '')

    # mostriamo tutti i prodotti se il filtro è vuoto, altrimenti solo quelli del tipo selezionato
    prodotti = db.prodotti_lista(tipo = tipo_filter or None)

    # otteniamo la lista dei tipi di prodotto per il filtro a tendina
    tipi = db.prodotti_tipi()

    # renderizziamo la pagina dei prodotti passando i prodotti filtrati, i tipi disponibili e lo stato del filtro
    return render_template('prodotti.html', prodotti=prodotti, tipi=tipi, tipo_filter=tipo_filter)


# rotta per aggiungere un nuovo prodotto, con validazione dei dati e gestione degli errori
@bp.route('/nuovo', methods=['GET', 'POST'])
def nuovo():
    # se è una richiesta POST, proviamo ad aggiungere il prodotto al database
    if request.method == 'POST':
        # estraiamo e validiamo i dati dal form
        nome = request.form['nome'].strip()
        tipo = request.form['tipo'].strip()
        prezzo = parse_float(request.form.get('prezzo'))
        quantita = parse_int(request.form.get('quantita'))
        soglia_minima = parse_int(request.form.get('soglia_minima', default=5))

        # validazione dei dati con messaggi di errore specifici per ogni campo
        if not nome:
            flash('Il nome del prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto = None, action = 'Aggiungi')
        if not tipo:
            flash('Il tipo di prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto = None, action = 'Aggiungi')
        if prezzo is None or prezzo < 0:
            flash('Prezzo non valido.', 'error')
            return render_template('prodotto_form.html', prodotto = None, action = 'Aggiungi')
        if quantita is None or quantita < 0:
            flash('Quantità non valida.', 'error')
            return render_template('prodotto_form.html', prodotto = None, action = 'Aggiungi')
        if soglia_minima is None or soglia_minima < 0:
            flash('Soglia minima non valida.', 'error')
            return render_template('prodotto_form.html', prodotto = None, action='Aggiungi')
        
        # inseriamo il prodotto nel database e otteniamo il codice generato
        _, codice = db.prodotto_insert(
            nome=nome,
            tipo=tipo,
            prezzo=prezzo,
            quantita=quantita,
            soglia_minima=soglia_minima,
        )

        # mostriamo un messaggio di successo e reindirizziamo alla lista dei prodotti
        flash(f'Prodotto "{nome}" aggiunto (codice {codice}).', 'success')
        return redirect(url_for('prodotti.lista'))
    
    # se è una richiesta GET, mostriamo il form vuoto per aggiungere un nuovo prodotto
    return render_template('prodotto_form.html', prodotto = None, action = 'Aggiungi')


# rotta per modificare un prodotto esistente, con validazione dei dati e gestione degli errori
@bp.route('/modifica/<int:id>', methods=['GET', 'POST'])
def modifica(id):
    # otteniamo il prodotto dal database
    prodotto = db.prodotto_get(id)

    # se il prodotto non esiste, mostriamo un messaggio di errore e reindirizziamo alla lista dei prodotti
    if not prodotto:
        flash('Prodotto non trovato.', 'error')
        return redirect(url_for('prodotti.lista'))

    # se è una richiesta POST, proviamo ad aggiornare il prodotto nel database
    if request.method == 'POST':
        # estraiamo e validiamo i dati dal form
        nome = request.form['nome'].strip()
        tipo = request.form['tipo'].strip()
        prezzo = parse_float(request.form.get('prezzo'))
        quantita = parse_int(request.form.get('quantita'))
        soglia_minima = parse_int(request.form.get('soglia_minima', default=5))

        # se il tipo è stato modificato, dobbiamo aggiornare anche il codice del prodotto per mantenere la coerenza
        if tipo.lower() != prodotto['tipo'].lower():
            nuovo_codice = db._codice_prodotto(tipo, id, data=None)
            # volendo preservare la data originale potremmo estrarla stringando `prodotto['codice']`.
            # estraiamo la data dal vecchio codice per mantenere la coerenza
            parti_vecchio_codice = prodotto['codice'].split('-')
            if len(parti_vecchio_codice) == 3:
                nuovo_codice = f"{db._tipo_prefix(tipo)}-{parti_vecchio_codice[1]}-{id:04d}"
        else:
            nuovo_codice = prodotto['codice']
        if not nome:
            flash('Il nome del prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto = prodotto, action = 'Modifica')
        if not tipo:
            flash('Il tipo di prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto = prodotto, action = 'Modifica')
        if prezzo is None or prezzo < 0:
            flash('Prezzo non valido.', 'error')
            return render_template('prodotto_form.html', prodotto = prodotto, action = 'Modifica')
        if quantita is None or quantita < 0:
            flash('Quantità non valida.', 'error')
            return render_template('prodotto_form.html', prodotto = prodotto, action = 'Modifica')
        if soglia_minima is None or soglia_minima < 0:
            flash('Soglia minima non valida.', 'error')
            return render_template('prodotto_form.html', prodotto = prodotto, action = 'Modifica')
        
        # aggiorniamo il prodotto nel database con i nuovi dati e il nuovo codice se necessario
        db.prodotto_update(
            id=id,
            codice=nuovo_codice,
            nome=nome,
            tipo=tipo,
            prezzo=prezzo,
            quantita=quantita,
            soglia_minima=soglia_minima,
        )

        # mostriamo un messaggio di successo e reindirizziamo alla lista dei prodotti
        flash(f'Prodotto "{nome}" aggiornato.', 'success')
        return redirect(url_for('prodotti.lista'))

    # se è una richiesta GET, mostriamo il form precompilato con i dati del prodotto da modificare
    return render_template('prodotto_form.html', prodotto = prodotto, action = 'Modifica')


# rotta per eliminare un prodotto, con gestione degli errori in caso di vincoli di integrità
@bp.route('/elimina/<int:id>', methods=['POST'])
def elimina(id):
    # otteniamo il prodotto dal database
    prodotto = db.prodotto_get(id)

    # se il prodotto non esiste, mostriamo un messaggio di errore e reindirizziamo alla lista dei prodotti
    if not prodotto:
        flash('Prodotto non trovato.', 'error')
        return redirect(url_for('prodotti.lista'))
    try:
        db.prodotto_delete(id)
        flash(f'Prodotto "{prodotto["nome"]}" eliminato.', 'success')
    except psycopg2.IntegrityError:
        flash('Impossibile eliminare: il prodotto è presente in vendite esistenti.', 'error')
    except Exception as e:
        flash(f'Si è verificato un errore del server durante l\'eliminazione.', 'error')

    # reindirizziamo alla lista dei prodotti dopo il tentativo di eliminazione
    return redirect(url_for('prodotti.lista'))