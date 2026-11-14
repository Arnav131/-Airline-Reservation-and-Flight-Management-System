-- ============================================================================
-- Experiment 1: Complex Multi-Table JOIN Queries & Available Seat Analytics
-- ============================================================================

USE iarfms_db;

-- Query 1: Retrieve Full Passenger Flight & Payment Itinerary (6-Table INNER/LEFT JOIN)
SELECT
    r.Reservation_ID,
    p.Name              AS Passenger_Name,
    p.Email,
    f.Flight_ID,
    src.City            AS Departure_City,
    src.Airport_ID      AS Origin_Code,
    dst.City            AS Arrival_City,
    dst.Airport_ID      AS Dest_Code,
    a.Aircraft_Model,
    f.Departure_Time,
    r.Seat_Number,
    r.Booking_Status,
    COALESCE(pay.Amount, 0.00) AS Paid_Amount,
    COALESCE(pay.Payment_Status, 'UNPAID') AS Payment_Status
FROM Reservations r
INNER JOIN Passengers p   ON r.Passenger_ID = p.Passenger_ID
INNER JOIN Flights f      ON r.Flight_ID    = f.Flight_ID
INNER JOIN Airports src   ON f.Source_Airport = src.Airport_ID
INNER JOIN Airports dst   ON f.Destination_Airport = dst.Airport_ID
INNER JOIN Aircraft a     ON f.Aircraft_ID  = a.Aircraft_ID
LEFT JOIN  Payments pay   ON r.Reservation_ID = pay.Reservation_ID
ORDER BY f.Departure_Time ASC, r.Reservation_ID ASC;

-- Query 2: Identify Available Seats Per Flight (Capacity minus CONFIRMED reservations)
SELECT
    f.Flight_ID,
    f.Source_Airport,
    f.Destination_Airport,
    a.Aircraft_Model,
    a.Capacity AS Total_Capacity,
    COUNT(CASE WHEN r.Booking_Status = 'CONFIRMED' THEN 1 END) AS Booked_Seats,
    (a.Capacity - COUNT(CASE WHEN r.Booking_Status = 'CONFIRMED' THEN 1 END)) AS Available_Seats,
    ROUND((COUNT(CASE WHEN r.Booking_Status = 'CONFIRMED' THEN 1 END) / a.Capacity) * 100, 2) AS Occupancy_Pct
FROM Flights f
INNER JOIN Aircraft a ON f.Aircraft_ID = a.Aircraft_ID
LEFT JOIN Reservations r ON f.Flight_ID = r.Flight_ID
GROUP BY f.Flight_ID, f.Source_Airport, f.Destination_Airport, a.Aircraft_Model, a.Capacity
ORDER BY Available_Seats DESC;

-- Query 3: Flight Crew Assignment Roster
SELECT
    f.Flight_ID,
    f.Source_Airport,
    f.Destination_Airport,
    c.Name AS Crew_Member,
    c.Designation,
    ca.Duty_Role
FROM Flights f
INNER JOIN Crew_Assignments ca ON f.Flight_ID = ca.Flight_ID
INNER JOIN Crew c              ON ca.Crew_ID  = c.Crew_ID
ORDER BY f.Flight_ID, c.Crew_ID;

-- Query 4: Identify Flights Without Any Confirmed Bookings (LEFT JOIN Anti-Pattern)
SELECT
    f.Flight_ID,
    f.Source_Airport,
    f.Destination_Airport,
    f.Departure_Time
FROM Flights f
LEFT JOIN Reservations r
    ON f.Flight_ID = r.Flight_ID AND r.Booking_Status = 'CONFIRMED'
WHERE r.Reservation_ID IS NULL;
