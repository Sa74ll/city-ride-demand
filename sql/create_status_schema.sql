
## create table and hypertable 
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE station_status (
  ts          TIMESTAMPTZ NOT NULL,
  station_id  TEXT        NOT NULL,
  bikes_free  INT         NOT NULL,
  docks_free  INT         NOT NULL,
  ingest_time TIMESTAMPTZ NOT NULL DEFAULT now()
);

SELECT create_hypertable('station_status', 'ts', migrate_data => true);
CREATE INDEX ON station_status (station_id, ts DESC);

## test insert + query
INSERT INTO station_status (ts, station_id, bikes_free, docks_free)
VALUES (now(), 'TEST_001', 8, 15);

SELECT * FROM station_status LIMIT 1;
