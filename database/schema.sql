CREATE TABLE "ShoppingCart" (
  "node_id" varchar(20) PRIMARY KEY,
  "description" varchar(50)
);

CREATE TABLE "Visit" (
  "visit_id" int PRIMARY KEY,
  "node_id" varchar(20),
  "duration" interval,
  "start_time" timestamp,
  "end_time" timestamp
);

CREATE TABLE "Zone" (
  "zone_id" serial PRIMARY KEY,
  "visit_id" int,
  "x" float,
  "y" float,
  "timestamp" timestamp
);

CREATE TABLE "Categories" (
  "category_id" int PRIMARY KEY,
  "name" varchar,
  "x_min" float,
  "x_max" float,
  "y_min" float,
  "y_max" float
);

CREATE TABLE "ZoneVisit" (
  "zone_visit_id" int PRIMARY KEY,
  "visit_id" int,
  "category_id" int,
  "start_time" timestamp,
  "end_time" timestamp
);

CREATE TABLE "Quality" (
  "quality_id" serial PRIMARY KEY,
  "node_id" varchar(20),
  "zone_id" int,
  "is_valid" boolean,
  "reason" varchar NOT NULL,
  "more_info" varchar
);

ALTER TABLE "Visit" ADD FOREIGN KEY ("node_id") REFERENCES "ShoppingCart" ("node_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ZoneVisit" ADD FOREIGN KEY ("visit_id") REFERENCES "Visit" ("visit_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "ZoneVisit" ADD FOREIGN KEY ("category_id") REFERENCES "Categories" ("category_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "Zone" ADD FOREIGN KEY ("visit_id") REFERENCES "Visit" ("visit_id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "Zone" ADD FOREIGN KEY ("zone_id") REFERENCES "Quality" ("zone_id") DEFERRABLE INITIALLY IMMEDIATE;
