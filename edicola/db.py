# --- GESTIONE DELLA CONNESSIONE AL DATABASE E OPERAZIONI SQL ---

import re
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from datetime import datetime
from config import Config
from decimal import Decimal, ROUND_HALF_UP


# --- UTILITY ---
# funzione per ottenere una connessione al database, usata in tutti i metodi che accedono al database
# usa i parametri da Config.DB_PARAMS
@contextmanager
def get_conn():
    conn = psycopg2.connect(**Config.DB_PARAMS)
    try:
        yield conn
    finally:
        conn.close()


# funzione per convertire qualsiasi valore numerico in Decimal con 2 decimali, usando arrotondamento HALF_UP
def _to_decimal(val):
    return Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# --- PRODOTTI ---
# codice prodotto generato automaticamente con formato TIPO-DATA-ID
_TIPO_PREFIX_MAP = {
    "giornale": "GIO",
    "rivista": "RIV",
    "fumetto": "FUM",
    "libro": "LIB",
    "altro": "ALT",
}


# funzione per definire il prefisso del codice prodotto
def _tipo_prefix(tipo):
    # se il tipo è mancante o vuoto, uso "GEN" per generico
    if not tipo:
        return "GEN"
    key = tipo.strip().lower()

    # se il tipo è nella mappa, uso il prefisso definito, altrimenti genero un prefisso pulito dai primi 3 caratteri del tipo
    if key in _TIPO_PREFIX_MAP:
        return _TIPO_PREFIX_MAP[key]
    cleaned = re.sub(r"[^a-z0-9]", "", key)

    # se dopo la pulizia rimangono almeno 3 caratteri, uso i primi 3, altrimenti uso quelli disponibili e completo con "X"
    if len(cleaned) >= 3:
        return cleaned[:3].upper()
    
    # se il tipo è troppo corto o non ha caratteri validi, uso "GEN" per generico
    if cleaned:
        return cleaned.upper().ljust(3, "X")
    
    return "GEN"


# funzione per generare il codice prodotto a partire dal tipo
def _codice_prodotto(tipo, prodotto_id, data=None):
    data = data or datetime.now()       # se non viene fornita una data, uso quella corrente

    data_str = data.strftime("%d%m%y")  # formato DDMMYY per la data

    return f"{_tipo_prefix(tipo)}-{data_str}-{prodotto_id:04d}"


# funzione per ottenere la lista intera dei prodotti, con filtro opzionale per tipo, e flag scorta bassa
def prodotti_lista(tipo=None):
    sql = """
        SELECT id, codice, nome, tipo, prezzo, quantita, soglia_minima, (quantita < soglia_minima) AS scorta_bassa
        FROM prodotti
    """

    # costruisco dinamicamente la clausola WHERE se viene specificato un filtro per tipo
    params = []
    if tipo:
        sql += " WHERE tipo = %s"
        params.append(tipo)

    # ordino sempre per nome prodotto in modo consistente, indipendentemente dal filtro
    sql += " ORDER BY nome"

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


# funzione per ottenere la lista dei tipi di prodotto distinti 
def prodotti_tipi():
    sql = """
        SELECT DISTINCT tipo 
        FROM prodotti 
        ORDER BY tipo
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [r[0] for r in cur.fetchall()]


# funzione per ottenere un singolo prodotto per id
def prodotto_get(id):
    sql = """
        SELECT * 
        FROM prodotti 
        WHERE id = %s
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (id,))
            return cur.fetchone()


# funzione per inserire un nuovo prodtto
def prodotto_insert(nome, tipo, prezzo, quantita, soglia_minima, codice = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if codice and codice.strip():
                cur.execute(
                    """
                    INSERT INTO prodotti (codice, nome, tipo, prezzo, quantita, soglia_minima)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (codice, nome, tipo, prezzo, quantita, soglia_minima),
                )
                new_id = cur.fetchone()[0]
                conn.commit()
                return new_id, codice

            cur.execute("SELECT nextval(pg_get_serial_sequence('prodotti', 'id'))")
            new_id = cur.fetchone()[0]
            codice = _codice_prodotto(tipo, new_id)
            cur.execute(
                """
                INSERT INTO prodotti (id, codice, nome, tipo, prezzo, quantita, soglia_minima)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (new_id, codice, nome, tipo, prezzo, quantita, soglia_minima),
            )
        conn.commit()
    return new_id, codice


# funzione per aggiornare un prodotto esistente
def prodotto_update(id, codice, nome, tipo, prezzo, quantita, soglia_minima):
    sql = """
        UPDATE prodotti
        SET codice=%s, nome=%s, tipo=%s, prezzo=%s, quantita=%s, soglia_minima=%s
        WHERE id=%s
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (codice, nome, tipo, prezzo, quantita, soglia_minima, id))
        conn.commit()


# funzione per eliminare un prodotto (fallisce se ci sono dettagli_vendita collegate)
def prodotto_delete(id):
    sql = """
        DELETE FROM prodotti 
        WHERE id = %s
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id,))
        conn.commit()


# funzione per ottenere la lista dei prodotti, con filtro opzionale per tipo e flag scorta bassa
def prodotti_scorta_bassa(tipo=None, solo_scorta_bassa=False):
    sql = """
        SELECT id, codice, nome, tipo, prezzo, quantita, soglia_minima, (quantita < soglia_minima) AS scorta_bassa
        FROM prodotti
        WHERE 1=1
    """

    # costruisco dinamicamente la clausola WHERE se viene specificato un filtro per tipo o se voglio solo quelli a scorta bassa
    params = []
    if tipo:
        sql += " AND tipo = %s"
        params.append(tipo)

    # se voglio solo quelli a scorta bassa, aggiungo la condizione alla query
    if solo_scorta_bassa:
        sql += " AND quantita < soglia_minima"
    sql += " ORDER BY nome"

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


# funzione per contare quanti prodotti sono sotto la soglia minima
def count_scorta_bassa():
    sql = """
        SELECT COUNT(*)
        FROM prodotti
        WHERE quantita < soglia_minima
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()[0]


# --- VENDITE ---
# funzione per registrare una vendita completa in una transazione
def vendita_insert(righe):
    with get_conn() as conn:
        with conn.cursor() as cur:
            # 1. crea la testata vendita
            cur.execute(
                "INSERT INTO vendite (data_ora, totale) VALUES (NOW(), 0) RETURNING id"
            )
            vendita_id = cur.fetchone()[0]  # ottengo l'id generato per la vendita
 
            totale = Decimal('0.00')        # variabile per calcolare il totale della vendita

            # per ogni riga della vendita, inserisco i dettagli e aggiorno le scorte, tutto dentro la stessa transazione
            for riga in righe:
                pid = riga['prodotto_id']
                qty = riga['quantita']

                # leggi prezzo corrente
                cur.execute(
                    """
                    SELECT prezzo, quantita 
                    FROM prodotti 
                    WHERE id = %s FOR UPDATE
                    """,
                    (pid,)
                )
                row = cur.fetchone()    
                if not row:
                    raise ValueError(f"Prodotto {pid} non trovato.")
                
                prezzo_unit, disponibile = row                  # ottengo prezzo e quantità disponibile
                prezzo_decimal = _to_decimal(prezzo_unit)       # converto il prezzo in Decimal con 2 decimali
                subtotale = _to_decimal(prezzo_decimal * qty)   # calcolo il subtotale per la riga

                # controllo se la quantità richiesta è disponibile, altrimenti sollevo un errore per rollback
                if disponibile < qty:
                    raise ValueError(
                        f"Quantità insufficiente per prodotto id={pid} "
                        f"(richiesta {qty}, disponibile {disponibile})."
                    )

                # 2. INSERT riga vendita
                cur.execute(
                    """
                    INSERT INTO dettagli_vendita (vendita_id, prodotto_id, quantita, prezzo_unitario, subtotale)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (vendita_id, pid, qty, prezzo_decimal, subtotale)
                )

                # 3. UPDATE scorte prodotto
                cur.execute(
                    """
                    UPDATE prodotti 
                    SET quantita = quantita - %s 
                    WHERE id = %s
                    """,
                    (qty, pid)
                )

                totale += subtotale

            # 4. UPDATE totale vendita
            cur.execute(
                """
                UPDATE vendite 
                SET totale = %s 
                WHERE id = %s
                """,
                (totale, vendita_id)
            )

        conn.commit()

    return vendita_id


# funzione per ottenere la lista delle vendite, con conteggio righe vendita e ordinamento per data decrescente
def vendite_lista(limit=50):
    sql = """
        SELECT v.id, v.data_ora, v.totale, COUNT(rv.id) AS n_articoli
        FROM vendite v
        LEFT JOIN dettagli_vendita rv ON rv.vendita_id = v.id
        GROUP BY v.id, v.data_ora, v.totale
        ORDER BY data_ora DESC
        LIMIT %s
    """
    # uso LEFT JOIN perché una vendita senza righe deve comunque apparire nello storico con conteggio 0

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            return cur.fetchall()


# funzione per ottenere i dettagli di una vendita, con data e totale
def vendita_get(id):
    sql = """
        SELECT id, data_ora, totale 
        FROM vendite 
        WHERE id = %s
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (id,))
            return cur.fetchone()


# funzione per ottenere i dettagli di una vendita, con JOIN su prodotti per avere nome e tipo prodotto
def vendita_righe(vendita_id):
    sql = """
        SELECT rv.id, rv.quantita, rv.prezzo_unitario, rv.subtotale, p.id AS prodotto_id, 
            p.nome AS nome_prodotto, p.tipo AS tipo_prodotto, p.codice AS codice_prodotto
        FROM dettagli_vendita rv
        JOIN prodotti p ON p.id = rv.prodotto_id
        WHERE rv.vendita_id = %s
        ORDER BY rv.id
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (vendita_id,))
            return cur.fetchall()


# --- REPORT ---
# funzione per ottenere il totale e il numero di vendite in un periodo specificato
def report_totale(dt_inizio, dt_fine):
    sql = """
        WITH vendite_periodo AS (
            SELECT id, totale
            FROM vendite
            WHERE data_ora BETWEEN %s AND %s
        ),
        righe_periodo AS (
            SELECT rv.quantita
            FROM dettagli_vendita rv
            JOIN vendite_periodo vp ON vp.id = rv.vendita_id
        )
        SELECT
            COALESCE((SELECT SUM(totale) FROM vendite_periodo), 0) AS totale_periodo,
            (SELECT COUNT(*) FROM vendite_periodo) AS n_vendite,
            COALESCE((SELECT SUM(quantita) FROM righe_periodo), 0) AS articoli_venduti,
            COALESCE((SELECT AVG(totale) FROM vendite_periodo), 0) AS ticket_medio,
            COALESCE((SELECT MAX(totale) FROM vendite_periodo), 0) AS vendita_massima
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (dt_inizio, dt_fine))
            return cur.fetchone()


# funzione per ottenere la ripartizione del fatturato per tipo di prodotto nel periodo specificato
def report_ripartizione_tipi(dt_inizio, dt_fine):
    sql = """
        SELECT p.tipo,
               COALESCE(SUM(rv.quantita), 0) AS quantita_venduta,
               COALESCE(SUM(rv.subtotale), 0) AS fatturato,
               COUNT(DISTINCT rv.vendita_id) AS n_vendite
        FROM dettagli_vendita rv
        JOIN prodotti p ON p.id = rv.prodotto_id
        JOIN vendite  v ON v.id = rv.vendita_id
        WHERE v.data_ora BETWEEN %s AND %s
        GROUP BY p.tipo
        ORDER BY fatturato DESC, p.tipo
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (dt_inizio, dt_fine))
            return cur.fetchall()


# funzione per ottenere i prodotti più venduti in un periodo specificato, con quantità totale e importo totale, ordinati per quantità decrescente
def report_top_prodotti(dt_inizio, dt_fine, limit=10):
    sql = """
        SELECT p.nome, p.tipo, SUM(rv.quantita) AS tot_qty, SUM(rv.subtotale) AS tot_importo
        FROM dettagli_vendita rv
        JOIN prodotti p ON p.id = rv.prodotto_id
        JOIN vendite  v ON v.id = rv.vendita_id
        WHERE v.data_ora BETWEEN %s AND %s
        GROUP BY p.id, p.nome, p.tipo
        ORDER BY tot_qty DESC
        LIMIT %s
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (dt_inizio, dt_fine, limit))
            return cur.fetchall()


# funzione per ottenere la lista delle vendite nel periodo specificato, con data e totale, ordinati per data decrescente
def report_vendite_periodo(dt_inizio, dt_fine):
    sql = """
        SELECT v.id, v.data_ora, v.totale, COUNT(rv.id) AS n_righe, COALESCE(SUM(rv.quantita), 0) AS quantita_totale
        FROM vendite v
        LEFT JOIN dettagli_vendita rv ON rv.vendita_id = v.id
        WHERE v.data_ora BETWEEN %s AND %s
        GROUP BY v.id, v.data_ora, v.totale
        ORDER BY v.data_ora DESC
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (dt_inizio, dt_fine))
            return cur.fetchall()