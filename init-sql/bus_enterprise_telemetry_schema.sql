-- =============================================================================
-- Telemetry schema for bus_enterprise (ADDITIVE ONLY)
-- =============================================================================
-- This does NOT touch anything in core / biz / fin / system - no ALTER TABLE,
-- no new columns on existing tables, no triggers on existing tables. It only
-- creates a brand-new "telemetry" schema alongside the existing ones.
--
-- The one link to the existing schema is a nullable foreign key from
-- telemetry.buses.vehicle_id -> core.vehicles(id) - "nullable" because demo
-- bus_id values (e.g. "BUS-001") won't always match a real
-- registration_number, and unmatched rows should still be storable rather
-- than rejected.
--
-- rapid-route-primary-sync (a separate project) reads/writes these tables
-- but does NOT create them - this file is that schema, meant to be applied
-- to bus_enterprise once, by you, however fits your own migration process.
--
-- HOW TO APPLY THIS
-- ------------------
-- bus_db's docker-compose.yml mounts ./init-sql into
-- /docker-entrypoint-initdb.d, but Postgres only RUNS those scripts the
-- very first time a data volume initializes (an empty bus_db_data volume).
-- Since bus_db is already running with an existing volume, just adding
-- this file to init-sql will NOT retroactively apply it - Postgres won't
-- re-run init scripts against a volume that already has data.
--
-- Pick one:
--   1) Apply it manually, once, against the running database:
--        docker exec -i bus_enterprise_db psql -U postgres -d bus_enterprise < bus_enterprise_telemetry_schema.sql
--      (or via any SQL client - psql, DBeaver, pgAdmin - connected to
--      bus_enterprise; every statement is idempotent, so running it more
--      than once is harmless.)
--   2) ALSO drop a copy into init-sql for future fresh deployments (a new
--      environment starting from an empty volume) so it's applied
--      automatically from then on - keep it there in addition to (1), not
--      instead of it, for your already-running instance.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS telemetry;

-- Maps a telemetry bus_id (e.g. "BUS-001") to a real vehicle in the
-- enterprise schema, when one can be matched. rapid-route-primary-sync
-- fills this in by looking up core.vehicles.registration_number - adjust
-- that matching rule there if your real bus_id/plate scheme differs.
CREATE TABLE IF NOT EXISTS telemetry.buses (
    bus_id      TEXT PRIMARY KEY,
    vehicle_id  UUID REFERENCES core.vehicles(id),
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per telemetry event synced over from TimescaleDB - mirrors
-- bus_telemetry_events there (see rapid-route-timescaledb's schema), plus
-- the resolved vehicle_id for joining into the enterprise schema.
CREATE TABLE IF NOT EXISTS telemetry.bus_events (
    time        TIMESTAMPTZ NOT NULL,
    bus_id      TEXT        NOT NULL REFERENCES telemetry.buses(bus_id),
    vehicle_id  UUID        REFERENCES core.vehicles(id),
    event_type  TEXT        NOT NULL,
    payload     JSONB       NOT NULL,

    PRIMARY KEY (bus_id, time, event_type)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_bus_events_vehicle
    ON telemetry.bus_events (vehicle_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_bus_events_type
    ON telemetry.bus_events (event_type, time DESC);

-- Single-row watermark: how far rapid-route-primary-sync has read from
-- TimescaleDB so far. Kept in this DB (rather than in-memory in the sync
-- service) so a restart of that service resumes correctly without
-- re-reading or dropping rows.
CREATE TABLE IF NOT EXISTS telemetry.sync_state (
    id                  BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (id = TRUE),
    last_synced_time    TIMESTAMPTZ NOT NULL DEFAULT '1970-01-01Z'
);

INSERT INTO telemetry.sync_state (id) VALUES (TRUE)
ON CONFLICT (id) DO NOTHING;

-- Convenience view: latest event per bus, joined to the vehicle's real
-- registration/model where a match exists. Read-only, doesn't touch
-- anything - safe to drop/redefine any time.
CREATE OR REPLACE VIEW telemetry.v_latest_bus_status AS
SELECT DISTINCT ON (be.bus_id)
    be.bus_id,
    be.vehicle_id,
    v.registration_number,
    v.model,
    be.event_type,
    be.time,
    be.payload
FROM telemetry.bus_events be
LEFT JOIN core.vehicles v ON v.id = be.vehicle_id
ORDER BY be.bus_id, be.time DESC;
