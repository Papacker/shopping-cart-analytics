-- 1. Luodaan automaattiset laskurit (Sequences)
CREATE SEQUENCE IF NOT EXISTS zone_id_seq;
CREATE SEQUENCE IF NOT EXISTS quality_id_seq;
CREATE SEQUENCE IF NOT EXISTS zone_visit_id_seq;

-- 2. Ostoskärryt
CREATE TABLE IF NOT EXISTS ShoppingCart (
  node_id VARCHAR PRIMARY KEY,
  description VARCHAR
);

-- 3. Vierailut (Muutettu visit_id VARCHARiksi, koska final_sid on tekstiä)
CREATE TABLE IF NOT EXISTS Visit (
  visit_id VARCHAR PRIMARY KEY,
  node_id VARCHAR,
  duration_seconds BIGINT,
  start_time TIMESTAMP,
  end_time TIMESTAMP
);

-- 4. Paikannustiedot (Lisätty DEFAULT-laskuri)
CREATE TABLE IF NOT EXISTS Zone (
  zone_id BIGINT PRIMARY KEY DEFAULT nextval('zone_id_seq'),
  visit_id VARCHAR,
  x DOUBLE,
  y DOUBLE,
  timestamp TIMESTAMP
);

-- 5. Kategoriat
CREATE TABLE IF NOT EXISTS Categories (
  category_id BIGINT PRIMARY KEY,
  name VARCHAR NOT NULL,
  x_min DOUBLE, x_max DOUBLE, y_min DOUBLE, y_max DOUBLE
);

-- 6. Kärryn viipymä osastolla
CREATE TABLE IF NOT EXISTS ZoneVisit (
  zone_visit_id BIGINT PRIMARY KEY DEFAULT nextval('zone_visit_id_seq'),
  visit_id VARCHAR,
  category_id BIGINT,
  start_time TIMESTAMP,
  end_time TIMESTAMP
);

-- 7. Laadunvalvonta
CREATE TABLE IF NOT EXISTS Quality (
  quality_id BIGINT PRIMARY KEY DEFAULT nextval('quality_id_seq'),
  node_id VARCHAR,
  zone_id BIGINT,
  is_valid BOOLEAN,
  reason VARCHAR NOT NULL,
  more_info VARCHAR
);