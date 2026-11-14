-- ============================================================================
-- Experiment 1: Transaction Control Language (TCL) - COMMIT, ROLLBACK, SAVEPOINT
-- ============================================================================

USE iarfms_db;

-- Scenario: Booking a flight ticket using SAVEPOINT for partial recovery
START TRANSACTION;

-- Step 1: Insert new passenger reservation (initially PENDING)
INSERT INTO Reservations (Reservation_ID, Passenger_ID, Flight_ID, Seat_Number, Booking_Status)
VALUES (1009, 101, 'AI-304', '07A', 'PENDING');

SAVEPOINT sp_reservation_created;

-- Step 2: Attempt payment processing
INSERT INTO Payments (Payment_ID, Reservation_ID, Amount, Payment_Status)
VALUES (5009, 1009, 4100.00, 'FAILED');

-- Simulate business check: payment failed, so rollback ONLY the failed payment and keep/retry or rollback whole txn
ROLLBACK TO SAVEPOINT sp_reservation_created;

-- Step 3: Retry payment successfully
INSERT INTO Payments (Payment_ID, Reservation_ID, Amount, Payment_Status)
VALUES (5010, 1009, 4100.00, 'SUCCESS');

-- Step 4: Confirm reservation
UPDATE Reservations
SET Booking_Status = 'CONFIRMED'
WHERE Reservation_ID = 1009;

COMMIT;

-- Verify committed state
SELECT r.Reservation_ID, r.Flight_ID, r.Seat_Number, r.Booking_Status, p.Payment_ID, p.Payment_Status
FROM Reservations r
JOIN Payments p ON r.Reservation_ID = p.Reservation_ID
WHERE r.Reservation_ID = 1009;
