-- ============================================================================
-- Experiment 3.1: Performance Optimization - EXPLAIN Analysis (MySQL 8.0)
-- ============================================================================
USE iarfms_db;

-- 1. Analyze Flight Search Query (Source + Destination + Departure Time)
EXPLAIN ANALYZE
SELECT Flight_ID, Departure_Time, Base_Fare, Flight_Status
FROM Flights
WHERE Source_Airport = 'DEL'
  AND Destination_Airport = 'BOM'
  AND Departure_Time >= '2026-11-12 00:00:00';

-- 2. Analyze Reservation Lookup by Flight_ID
EXPLAIN ANALYZE
SELECT Reservation_ID, Passenger_ID, Seat_Number, Booking_Status
FROM Reservations
WHERE Flight_ID = 'AI-202' AND Booking_Status = 'CONFIRMED';

-- 3. Analyze Reservation History Lookup by Passenger_ID
EXPLAIN ANALYZE
SELECT r.Reservation_ID, f.Flight_ID, f.Departure_Time, r.Seat_Number, r.Booking_Status
FROM Reservations r
JOIN Flights f ON r.Flight_ID = f.Flight_ID
WHERE r.Passenger_ID = 101;
