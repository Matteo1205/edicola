-- ============================================================
--  SCHEMA LOGICO DATABASE - Gestione Edicola
-- ============================================================
--
--  Tabelle:
--    1. prodotti       → catalogo e inventario
--    2. vendite        → testata di ogni scontrino
--    3. dettagli_vendita  → dettaglio prodotti venduti (JOIN)
--
--  Relazioni:
--    dettagli_vendita.prodotto_id  → prodotti.id   (N:1)
--    dettagli_vendita.vendita_id   → vendite.id    (N:1)
-- ============================================================

-- Cancella (nell'ordine giusto per i vincoli FK)
DROP TABLE IF EXISTS dettagli_vendita;
DROP TABLE IF EXISTS vendite;
DROP TABLE IF EXISTS prodotti;

-- ============================================================
--  TABELLA 1: prodotti
-- ============================================================
CREATE TABLE prodotti (
    id             SERIAL PRIMARY KEY,
    codice         VARCHAR(15)    NOT NULL UNIQUE,
    nome           VARCHAR(150)   NOT NULL,
    tipo           VARCHAR(50)    NOT NULL,          -- es. Giornale, Rivista, Fumetto
    prezzo         NUMERIC(10,2)  NOT NULL CHECK (prezzo >= 0),
    quantita       INTEGER        NOT NULL DEFAULT 0 CHECK (quantita >= 0),
    soglia_minima  INTEGER        NOT NULL DEFAULT 5 CHECK (soglia_minima >= 0)
);

-- ============================================================
--  TABELLA 2: vendite
-- ============================================================
CREATE TABLE vendite (
    id        SERIAL PRIMARY KEY,
    data_ora  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    totale    NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (totale >= 0)
);

-- ============================================================
--  TABELLA 3: dettagli_vendita
--  Tabella ponte tra vendite e prodotti (N:M risolto)
-- ============================================================
CREATE TABLE dettagli_vendita (
    id               SERIAL PRIMARY KEY,
    vendita_id       INTEGER        NOT NULL REFERENCES vendite(id)  ON DELETE CASCADE,
    prodotto_id      INTEGER        NOT NULL REFERENCES prodotti(id) ON DELETE RESTRICT,
    quantita         INTEGER        NOT NULL CHECK (quantita > 0),
    prezzo_unitario  NUMERIC(10,2)  NOT NULL CHECK (prezzo_unitario >= 0),
    subtotale        NUMERIC(10,2)  NOT NULL CHECK (subtotale >= 0)
);

-- Indici sulle FK per velocizzare i JOIN
CREATE INDEX idx_dettagli_vendita_id   ON dettagli_vendita(vendita_id);
CREATE INDEX idx_dettagli_prodotto_id  ON dettagli_vendita(prodotto_id);
CREATE INDEX idx_prodotti_tipo      ON prodotti(tipo);