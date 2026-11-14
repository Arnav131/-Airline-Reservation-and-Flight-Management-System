-- ============================================================================
-- Experiment 3.2: B-Tree Indexes & Computed Hash Column (MySQL 8.0)
-- ============================================================================
USE iarfms_db;

-- 1. B-Tree Indexes on Flight_ID and Passenger_ID in Reservations
CREATE INDEX idx_res_flight_id    ON Reservations (Flight_ID) USING BTREE;
CREATE INDEX idx_res_passenger_id ON Reservations (Passenger_ID) USING BTREE;

-- 2. Composite B-Tree Index for Flight Search (Leftmost Prefix Match)
CREATE INDEX idx_flights_route_time ON Flights (Source_Airport, Destination_Airport, Departure_Time) USING BTREE;

-- 3. Computed Stored Hash Column for Ticket Reference Lookup
ALTER TABLE Reservations
ADD COLUMN Ticket_Ref_Hash CHAR(64)
GENERATED ALWAYS AS (
    SHA2(CONCAT(Reservation_ID, '-', Passenger_ID, '-', Flight_ID, '-', Seat_Number), 256)
) STORED;

-- Index the Computed Hash Column for O(log N) / O(1) instant lookup
CREATE UNIQUE INDEX idx_res_ticket_hash ON Reservations (Ticket_Ref_Hash);

-- Verify fast ticket lookup using the computed hash
EXPLAIN
SELECT Reservation_ID, Passenger_ID, Flight_ID, Seat_Number, Booking_Status
FROM Reservations
WHERE Ticket_Ref_Hash = SHA2('1001-101-AI-202-12A', 256);
