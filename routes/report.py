from flask import Blueprint, render_template, request
from datetime import datetime, timedelta, date
import db

# blueprint per la gestione dei report
bp = Blueprint('report', __name__, url_prefix='/report')


# tipi di report disponibili per il filtro a tendina
_TIPI_PERIODO = {
    'giorno': 'Giorno',
    'settimana': 'Settimana',
    'mese': 'Mese',
    'anno': 'Anno',
}


# funzione per calcolare le date di inizio e fine del periodo in base al tipo selezionato
def _ultimo_giorno_mese(riferimento):
    if riferimento.month == 12:
        primo_giorno_mese_successivo = riferimento.replace(year=riferimento.year + 1, month=1, day=1)
    else:
        primo_giorno_mese_successivo = riferimento.replace(month=riferimento.month + 1, day=1)
    return primo_giorno_mese_successivo - timedelta(days=1)


# funzioni per passare le date dai parametri della query string, con gestione dei formati e dei valori non validi
def _parse_data(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, '%Y-%m-%d').date()
    except ValueError:
        return None


# funzione per convertire una stringa del formato "YYYY-Www" in una data che rappresenta il primo giorno della settimana corrispondente
def _parse_settimana(val):
    if not val:
        return None
    parts = val.split('-W')
    if len(parts) != 2:
        return None
    try:
        anno = int(parts[0])
        settimana = int(parts[1])
        return date.fromisocalendar(anno, settimana, 1)
    except (ValueError, TypeError):
        return None


# funzione per convertire una stringa del formato "YYYY-MM" in una data che rappresenta il primo giorno del mese corrispondente
def _parse_mese(val):
    if not val:
        return None
    parts = val.split('-')
    if len(parts) != 2:
        return None
    try:
        anno = int(parts[0])
        mese = int(parts[1])
        return date(anno, mese, 1)
    except (ValueError, TypeError):
        return None


# funzione per convertire una stringa del formato "YYYY" in una data che rappresenta il primo giorno dell'anno corrispondente
def _parse_anno(val):
    if not val:
        return None
    try:
        anno = int(str(val).strip())
        return date(anno, 1, 1)
    except (ValueError, TypeError):
        return None


# funzione per calcolare la data del primo giorno della settimana a cui appartiene una data di riferimento
def _inizio_settimana(riferimento):
    return riferimento - timedelta(days=riferimento.weekday())


# funzioni per convertire le date in stringhe da usare come valori degli input nei filtri
def _week_input_value(riferimento):
    iso_year, iso_week, _ = riferimento.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


# funzione per convertire una data in una stringa del formato "YYYY-MM" da usare come valore dell'input del filtro per il mese
def _month_input_value(riferimento):
    return f"{riferimento.year}-{riferimento.month:02d}"


# rotta per visualizzare il report, con filtro per periodo e gestione dei dati da mostrare
@bp.route('/')
def index():
    # recupera il tipo di periodo selezionato dal filtro a tendina, con default 'giorno'
    tipo_raw = request.args.get('periodo', 'giorno')
    tipo_alias = {
        'giornaliero': 'giorno',
        'settimanale': 'settimana',
        'mensile': 'mese',
    }
    tipo = tipo_alias.get(tipo_raw, tipo_raw)

    # se il tipo selezionato non è valido, usiamo 'giorno' come default
    if tipo not in _TIPI_PERIODO:
        tipo = 'giorno'

    # recupera le date di riferimento per il periodo selezionato dai parametri della query string, con gestione dei formati e dei valori non validi
    oggi = date.today()
    giorno_sel = _parse_data(request.args.get('giorno')) or oggi
    settimana_sel = _parse_settimana(request.args.get('settimana')) or _inizio_settimana(oggi)
    mese_sel = _parse_mese(request.args.get('mese')) or oggi.replace(day=1)
    anno_sel = _parse_anno(request.args.get('anno')) or date(oggi.year, 1, 1)

    # calcola le date di inizio e fine del periodo da usare per filtrare i dati del report in base al tipo selezionato
    if tipo == 'settimana':
        inizio = settimana_sel
        fine = inizio + timedelta(days=6)
    elif tipo == 'mese':
        inizio = mese_sel
        fine = _ultimo_giorno_mese(inizio)
    elif tipo == 'anno':
        inizio = anno_sel
        fine = date(inizio.year, 12, 31)
    else:
        inizio = giorno_sel
        fine = giorno_sel
    
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
        giorno_str=giorno_sel.isoformat(),
        settimana_str=_week_input_value(settimana_sel),
        mese_str=_month_input_value(mese_sel),
        anno_str=str(anno_sel.year),
        inizio=inizio,
        fine=fine,
        stats=stats,
        top_prodotti=top_prodotti,
        top_tipi=top_tipi,
        vendite=vendite,
    )
