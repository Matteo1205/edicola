from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.utils import parse_int, parse_float
import db

bp = Blueprint('prodotti', __name__, url_prefix='/prodotti')


@bp.route('/')
def lista():
    tipo_filter = request.args.get('tipo', '')
    prodotti = db.prodotti_lista(tipo=tipo_filter or None)
    tipi = db.prodotti_tipi()
    return render_template('prodotti.html', prodotti=prodotti, tipi=tipi, tipo_filter=tipo_filter)


@bp.route('/nuovo', methods=['GET', 'POST'])
def nuovo():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        tipo = request.form['tipo'].strip()
        prezzo = parse_float(request.form.get('prezzo'))
        quantita = parse_int(request.form.get('quantita'))
        soglia_minima = parse_int(request.form.get('soglia_minima', default=5))

        if not nome:
            flash('Il nome del prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto=None, action='Aggiungi')
        if not tipo:
            flash('Il tipo di prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto=None, action='Aggiungi')
        if prezzo is None or prezzo < 0:
            flash('Prezzo non valido.', 'error')
            return render_template('prodotto_form.html', prodotto=None, action='Aggiungi')
        if quantita is None or quantita < 0:
            flash('Quantità non valida.', 'error')
            return render_template('prodotto_form.html', prodotto=None, action='Aggiungi')
        if soglia_minima is None or soglia_minima < 0:
            flash('Soglia minima non valida.', 'error')
            return render_template('prodotto_form.html', prodotto=None, action='Aggiungi')
        _, codice = db.prodotto_insert(
            nome=nome,
            tipo=tipo,
            prezzo=prezzo,
            quantita=quantita,
            soglia_minima=soglia_minima,
        )
        flash(f'Prodotto "{nome}" aggiunto (codice {codice}).', 'success')
        return redirect(url_for('prodotti.lista'))
    return render_template('prodotto_form.html', prodotto=None, action='Aggiungi')


@bp.route('/modifica/<int:id>', methods=['GET', 'POST'])
def modifica(id):
    prodotto = db.prodotto_get(id)
    if not prodotto:
        flash('Prodotto non trovato.', 'error')
        return redirect(url_for('prodotti.lista'))

    if request.method == 'POST':
        nuovo_codice = prodotto['codice']
        nome = request.form['nome'].strip()
        tipo = request.form['tipo'].strip()
        prezzo = parse_float(request.form.get('prezzo'))
        quantita = parse_int(request.form.get('quantita'))
        soglia_minima = parse_int(request.form.get('soglia_minima', default=5))

        if not nome:
            flash('Il nome del prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto=prodotto, action='Modifica')
        if not tipo:
            flash('Il tipo di prodotto è obbligatorio.', 'error')
            return render_template('prodotto_form.html', prodotto=prodotto, action='Modifica')
        if prezzo is None or prezzo < 0:
            flash('Prezzo non valido.', 'error')
            return render_template('prodotto_form.html', prodotto=prodotto, action='Modifica')
        if quantita is None or quantita < 0:
            flash('Quantità non valida.', 'error')
            return render_template('prodotto_form.html', prodotto=prodotto, action='Modifica')
        if soglia_minima is None or soglia_minima < 0:
            flash('Soglia minima non valida.', 'error')
            return render_template('prodotto_form.html', prodotto=prodotto, action='Modifica')
        db.prodotto_update(
            id=id,
            codice=nuovo_codice,
            nome=nome,
            tipo=tipo,
            prezzo=prezzo,
            quantita=quantita,
            soglia_minima=soglia_minima,
        )
        flash(f'Prodotto "{nome}" aggiornato.', 'success')
        return redirect(url_for('prodotti.lista'))

    return render_template('prodotto_form.html', prodotto=prodotto, action='Modifica')


@bp.route('/elimina/<int:id>', methods=['POST'])
def elimina(id):
    prodotto = db.prodotto_get(id)
    if not prodotto:
        flash('Prodotto non trovato.', 'error')
        return redirect(url_for('prodotti.lista'))
    try:
        db.prodotto_delete(id)
        flash(f'Prodotto "{prodotto["nome"]}" eliminato.', 'success')
    except Exception:
        flash('Impossibile eliminare: il prodotto è presente in vendite esistenti.', 'error')
    return redirect(url_for('prodotti.lista'))
