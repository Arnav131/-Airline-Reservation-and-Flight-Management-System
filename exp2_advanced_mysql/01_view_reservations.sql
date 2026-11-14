-- ============================================================================
-- Experiment 2.1: VIEW for Passenger Flight Reservations (MySQL 8.0)
-- ============================================================================
USE iarfms_db;

CREATE OR REPLACE VIEW v_passenger_reservations AS
SELECT
    r.Reservation_ID,
    p.Passenger_ID,
    p.Name              AS Passenger_Name,
    p.Email             AS Passenger_Email,
    f.Flight_ID,
    src.Airport_ID      AS Origin_Code,
    src.City            AS Origin_City,
    dst.Airport_ID      AS Dest_Code,
    dst.City            AS Dest_City,
    a.Aircraft_Model,
    f.Departure_Time,
    f.Flight_Status,
    r.Seat_Number,
    r.Booking_Status,
    COALESCE(pay.Amount, 0.00)              AS Ticket_Amount,
    COALESCE(pay.Payment_Status, 'UNPAID')  AS Payment_Status
FROM Reservations r
INNER JOIN Passengers p ON r.Passenger_ID = p.Passenger_ID
INNER JOIN Flights f    ON r.Flight_ID    = f.Flight_ID
INNER JOIN Airports src ON f.Source_Airport = src.Airport_ID
INNER JOIN Airports dst ON f.Destination_Airport = dst.Airport_ID
INNER JOIN Aircraft a   ON f.Aircraft_ID  = a.Aircraft_ID
LEFT JOIN  Payments pay ON r.Reservation_ID = pay.Reservation_ID;

-- Query the view
SELECT * FROM v_passenger_reservations WHERE Booking_Status = 'CONFIRMED';
