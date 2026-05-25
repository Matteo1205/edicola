import db
from flask import Blueprint, render_template, request

# blueprint per la gestione dell'inventario
bp = Blueprint('inventario', __name__, url_prefix='/inventario')


# rotta per visualizzare l'inventario, con filtro per tipo e scorta bassa
@bp.route('/')
def index():
    # otteniamo i parametri di filtro
    tipo_filter = request.args.get('tipo', '')
    solo_scorta_bassa = request.args.get('scorta_bassa', '') == '1'

    # se è attivo il filtro per scorta bassa, mostriamo solo i prodotti con quantità <= soglia minima
    prodotti = db.prodotti_scorta_bassa(tipo = tipo_filter or None, solo_scorta_bassa = solo_scorta_bassa)

    # otteniamo la lista dei tipi di prodotto per il filtro a tendina
    tipi = db.prodotti_tipi()
    n_scorta_bassa = db.count_scorta_bassa()

    # renderizziamo la pagina dell'inventario passando i prodotti filtrati, i tipi disponibili e lo stato del filtro
    return render_template(
        'inventario.html',
        prodotti=prodotti,
        tipi=tipi,
        tipo_filter=tipo_filter,
        solo_scorta_bassa=solo_scorta_bassa,
        n_scorta_bassa=n_scorta_bassa,
    )
