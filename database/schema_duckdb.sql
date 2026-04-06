-- Ostoskärryt
CREATE TABLE IF NOT EXISTS ShoppingCart (
  node_id VARCHAR(20) PRIMARY KEY,
  description VARCHAR(50)
);

-- Vierailut
CREATE SEQUENCE IF NOT EXISTS visit_seq;
CREATE TABLE IF NOT EXISTS Visit (
  visit_id BIGINT DEFAULT nextval('visit_seq') PRIMARY KEY,
  node_id VARCHAR(20) NOT NULL,
  event_time BIGINT NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL,
  FOREIGN KEY (node_id) REFERENCES ShoppingCart(node_id)
);

-- Paikannustiedot
CREATE SEQUENCE IF NOT EXISTS zone_seq;
CREATE TABLE IF NOT EXISTS Zone (
  zone_id BIGINT DEFAULT nextval('zone_seq') PRIMARY KEY,
  visit_id BIGINT NOT NULL,
  x FLOAT NOT NULL,        -- float koska ETL skaalaa cm → m
  y FLOAT NOT NULL,
  z FLOAT NOT NULL,
  q INTEGER NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  speed_cms FLOAT,         -- nopeus cm/s, NULL ensimmäiselle pisteelle
  distance_cm FLOAT,       -- matka edellisestä pisteestä
  FOREIGN KEY (visit_id) REFERENCES Visit(visit_id)
);

-- Kategoriat
CREATE TABLE IF NOT EXISTS Categories (
  category_id BIGINT PRIMARY KEY,
  name VARCHAR NOT NULL,
  x_min FLOAT NOT NULL,
  x_max FLOAT NOT NULL,
  y_min FLOAT NOT NULL,
  y_max FLOAT NOT NULL,
  z INTEGER NOT NULL
);

-- Kärryn käyttämä aika kategoriassa
CREATE SEQUENCE IF NOT EXISTS zone_visit_seq;
CREATE TABLE IF NOT EXISTS ZoneVisit (
  zone_visit_id BIGINT DEFAULT nextval('zone_visit_seq') PRIMARY KEY,
  visit_id BIGINT NOT NULL,
  category_id BIGINT NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL,
  FOREIGN KEY (visit_id) REFERENCES Visit(visit_id),
  FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);