from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.utils import parse_int
import db


# blueprint per le vendite
bp = Blueprint('vendite', __name__, url_prefix='/vendite')


# route per la lista delle vendite
@bp.route('/')
def lista():
    # recupera tutte le vendite con i dati necessari per la lista (JOIN clienti)
    vendite = db.vendite_lista()

    # se non ci sono vendite, reindirizza al form di nuova vendita
    if not vendite:
        return redirect(url_for('vendite.nuova'))

    # renderizza la pagina con la lista delle vendite
    return render_template('vendite.html', vendite=vendite)


# route per la creazione di una nuova vendita
@bp.route('/nuova', methods=['GET', 'POST'])
def nuova():
    # recupera i prodotti disponibili (quantità > 0) per il form di vendita
    prodotti = [p for p in db.prodotti_lista() if p['quantita'] > 0]

    # se è una richiesta POST, processa i dati del form
    if request.method == 'POST':
        # recupera le liste di prodotto_id e quantita dal form
        prodotto_ids = request.form.getlist('prodotto_id[]')
        quantita_list = request.form.getlist('quantita[]')

        # costruisce la lista di righe per la vendita, validando i dati
        righe = []
        for pid_str, qty_str in zip(prodotto_ids, quantita_list):
            # se il prodotto_id è vuoto, salta questa riga (non è stata selezionata)
            if not pid_str:
                continue

            # converte i valori in interi e valida
            pid = parse_int(pid_str)
            qty = parse_int(qty_str)

            # se il prodotto_id non è valido, mostra un errore
            if pid is None:
                flash('Prodotto non valido.', 'error')
                return render_template('vendita_form.html', prodotti=prodotti)
            if qty is None or qty < 0:
                flash('Quantità non valida.', 'error')
                return render_template('vendita_form.html', prodotti=prodotti)
            if qty > 0:
                righe.append({'prodotto_id': pid, 'quantita': qty})

        # se non ci sono righe valide, mostra un errore
        if not righe:
            flash('Seleziona almeno un prodotto con quantità > 0.', 'error')

            return render_template('vendita_form.html', prodotti=prodotti)

        # prova a inserire la vendita nel database, gestendo eventuali errori (es. quantità non disponibile)
        try:
            vendita_id = db.vendita_insert(righe)
            
            flash('Vendita registrata con successo!', 'success')

            return redirect(url_for('vendite.ricevuta', id=vendita_id))
        except ValueError as e:
            flash(str(e), 'error')

            return render_template('vendita_form.html', prodotti=prodotti)

    # se è una richiesta GET, mostra il form di vendita
    return render_template('vendita_form.html', prodotti=prodotti)


# route per visualizzare la ricevuta di una vendita
@bp.route('/ricevuta/<int:id>')
def ricevuta(id):
    # recupera i dati della vendita e le righe (con JOIN prodotti) per visualizzare la ricevuta
    vendita = db.vendita_get(id)

    # se la vendita non esiste, mostra un messaggio di errore e reindirizza alla lista delle vendite
    if not vendita:
        flash('Vendita non trovata.', 'error')

        return redirect(url_for('vendite.lista'))
    
    # recupera le righe della vendita con i dati dei prodotti (JOIN prodotti) per visualizzare la ricevuta
    righe = db.vendita_righe(id)

    # renderizza la pagina della ricevuta con i dati della vendita e le righe
    return render_template('ricevuta.html', vendita=vendita, righe=righe)
