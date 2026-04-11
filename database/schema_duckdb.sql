-- Huom: DuckDB ei tue rajoitteita (FK/PK), joten ne jätetään pois tai dokumentoidaan kommentteina
-- Tavoite: Optimoida lukeminen, prosessointi ja visualisointi DuckDB:n avulla

-- Ostoskärryt
CREATE TABLE ShoppingCart (
  node_id VARCHAR PRIMARY KEY,
  description VARCHAR
);

-- Vierailut (muutettu interval → BIGINT sekunteina)
CREATE TABLE Visit (
  visit_id BIGINT PRIMARY KEY,
  node_id VARCHAR,
  duration_seconds BIGINT,
  start_time TIMESTAMP,
  end_time TIMESTAMP
);

-- Paikannustiedot (muutettu float → DOUBLE, serial → BIGINT)
CREATE TABLE Zone (
  zone_id BIGINT PRIMARY KEY,
  visit_id BIGINT,
  x DOUBLE,
  y DOUBLE,
  timestamp TIMESTAMP
);

-- Kategoriat (muutettu float → DOUBLE)
CREATE TABLE Categories (
  category_id BIGINT PRIMARY KEY,
  name VARCHAR NOT NULL,
  x_min DOUBLE,
  x_max DOUBLE,
  y_min DOUBLE,
  y_max DOUBLE
);

-- Kärryn käyttämä aika kategoriassa
CREATE TABLE ZoneVisit (
  zone_visit_id BIGINT PRIMARY KEY,
  visit_id BIGINT,
  category_id BIGINT,
  start_time TIMESTAMP,
  end_time TIMESTAMP
);

-- Datan tarkastus
CREATE TABLE Quality (
  quality_id BIGINT PRIMARY KEY,
  node_id VARCHAR,
  zone_id BIGINT,
  is_valid BOOLEAN,
  reason VARCHAR NOT NULL,
  more_info VARCHAR
);