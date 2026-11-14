-- ============================================================================
-- Experiment 6.1: Apache Cassandra Wide-Column Schema (CQL 3.x)
-- Partition Key: Flight_ID (ensures all events for one flight sit on the same node)
-- Clustering Keys: event_timestamp DESC, event_id ASC
-- ============================================================================

CREATE KEYSPACE IF NOT EXISTS airline_telemetry
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 3
};

USE airline_telemetry;

-- Table 1: Flight Activity & Operational Telemetry Log
CREATE TABLE IF NOT EXISTS flight_activity_log (
    flight_id       TEXT,
    event_timestamp TIMESTAMP,
    event_id        UUID,
    event_type      TEXT,     -- e.g., SCHEDULED, BOARDING_OPEN, GATE_CHANGE, DEPARTED, LANDED
    airport_code    TEXT,
    operator_id     TEXT,
    metadata        MAP<TEXT, TEXT>,
    PRIMARY KEY ((flight_id), event_timestamp, event_id)
) WITH CLUSTERING ORDER BY (event_timestamp DESC, event_id ASC);

-- Table 2: Passenger Travel Event Stream (Partitioned by Flight_ID)
CREATE TABLE IF NOT EXISTS passenger_travel_events (
    flight_id       TEXT,
    event_timestamp TIMESTAMP,
    passenger_id    INT,
    seat_number     TEXT,
    event_stage     TEXT,     -- CHECKIN, SECURITY_PASS, BAG_DROP, BOARDED
    gate_number     TEXT,
    PRIMARY KEY ((flight_id), event_timestamp, passenger_id)
) WITH CLUSTERING ORDER BY (event_timestamp DESC, passenger_id ASC);

-- Sample Partition-Scoped Query (Fast Single-Partition Lookup)
-- SELECT * FROM flight_activity_log WHERE flight_id = 'AI-202' LIMIT 10;
