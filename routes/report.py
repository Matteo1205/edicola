from flask import Blueprint, render_template, request
from datetime import datetime, timedelta, date
import db

# blueprint per la gestione dei report
bp = Blueprint('report', __name__, url_prefix='/report')


# tipi di report disponibili per il filtro a tendina
_TIPI_PERIODO = {
    'giornaliero': 'Oggi',
    'settimanale': 'Questa settimana',
    'mensile': 'Questo mese',
}


# funzione per calcolare le date di inizio e fine del periodo in base al tipo selezionato
def _periodo(tipo):
    # calcola le date di inizio e fine del periodo in base al tipo selezionato
    oggi = date.today()

    # per il report settimanale, inizio è il lunedì della settimana corrente e fine è la domenica
    if tipo == 'settimanale':
        inizio = oggi - timedelta(days=oggi.weekday())
        fine = inizio + timedelta(days=6)
    # per il report mensile, inizio è il primo giorno del mese e fine è l'ultimo giorno del mese
    elif tipo == 'mensile':
        inizio = oggi.replace(day=1)
        fine = (oggi.replace(month=oggi.month % 12 + 1, day=1) - timedelta(days=1)) \
               if oggi.month < 12 else oggi.replace(day=31)
    # per il report giornaliero, inizio e fine sono entrambi oggi
    else:
        inizio = fine = oggi
    
    return inizio, fine


# rotta per visualizzare il report, con filtro per periodo e gestione dei dati da mostrare
@bp.route('/')
def index():
    # recupera il tipo di periodo selezionato dal filtro a tendina, con default 'giornaliero'
    tipo = request.args.get('periodo', 'giornaliero')

    if tipo not in _TIPI_PERIODO:
        tipo = 'giornaliero'

    # calcola le date di inizio e fine del periodo in base al tipo selezionato
    inizio, fine = _periodo(tipo)
    
    # per evitare problemi di timezone, convertiamo le date in datetime con timezone locale
    local_tz = datetime.now().astimezone().tzinfo
    dt_inizio = datetime.combine(inizio, datetime.min.time()).replace(tzinfo=local_tz)
    dt_fine = datetime.combine(fine, datetime.max.time()).replace(tzinfo=local_tz)

    # recupera i dati da mostrare nel report chiamando le funzioni del modulo db con le date di inizio e fine del periodo
    stats = db.report_totale(dt_inizio, dt_fine)
    top_prodotti = db.report_top_prodotti(dt_inizio, dt_fine)
    top_tipi = db.report_ripartizione_tipi(dt_inizio, dt_fine)
    vendite = db.report_vendite_periodo(dt_inizio, dt_fine)

    # recupera l'etichetta del periodo da mostrare nel titolo del report in base al tipo selezionato
    periodo_label = _TIPI_PERIODO[tipo]

    # renderizza il template del report passando i dati recuperati e le informazioni sul periodo selezionato
    return render_template(
        'report.html',
        tipo=tipo,
        periodo_label=periodo_label,
        inizio=inizio,
        fine=fine,
        stats=stats,
        top_prodotti=top_prodotti,
        top_tipi=top_tipi,
        vendite=vendite,
    )
