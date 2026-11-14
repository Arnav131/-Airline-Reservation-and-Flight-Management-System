-- ============================================================================
-- Experiment 2.4: STORED PROCEDURE to Book Flight Tickets Atomically
-- ============================================================================
USE iarfms_db;

DROP PROCEDURE IF EXISTS sp_book_flight_ticket;

DELIMITER $$

CREATE PROCEDURE sp_book_flight_ticket(
    IN  p_passenger_id   INT,
    IN  p_flight_id      VARCHAR(15),
    IN  p_seat_number    VARCHAR(10),
    IN  p_seat_class     VARCHAR(20),
    OUT p_reservation_id INT,
    OUT p_total_amount   DECIMAL(10, 2),
    OUT p_status_msg     VARCHAR(255)
)
BEGIN
    DECLARE v_capacity INT DEFAULT 0;
    DECLARE v_booked   INT DEFAULT 0;
    DECLARE v_dep_time DATETIME;
    DECLARE v_days_diff INT DEFAULT 5;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_reservation_id = -1;
        SET p_total_amount = 0.00;
        SET p_status_msg = 'BOOKING_FAILED: Transaction rolled back due to duplicate seat or constraint violation.';
    END;

    START TRANSACTION;

    -- 1. Lock flight aircraft capacity check
    SELECT a.Capacity, f.Departure_Time INTO v_capacity, v_dep_time
    FROM Flights f
    JOIN Aircraft a ON f.Aircraft_ID = a.Aircraft_ID
    WHERE f.Flight_ID = p_flight_id
    FOR SHARE;

    SELECT COUNT(*) INTO v_booked
    FROM Reservations
    WHERE Flight_ID = p_flight_id AND Booking_Status = 'CONFIRMED'
    FOR UPDATE;

    IF v_booked >= v_capacity THEN
        ROLLBACK;
        SET p_reservation_id = -1;
        SET p_total_amount = 0.00;
        SET p_status_msg = 'BOOKING_FAILED: Flight has reached maximum aircraft capacity.';
    ELSE
        -- 2. Calculate dynamic ticket charge using Function
        SET v_days_diff = GREATEST(0, DATEDIFF(v_dep_time, NOW()));
        SET p_total_amount = fn_calculate_ticket_charge(p_flight_id, p_seat_class, v_days_diff);

        -- 3. Insert Reservation (trg_prevent_duplicate_seat guards seat collisions)
        INSERT INTO Reservations (Passenger_ID, Flight_ID, Seat_Number, Booking_Status)
        VALUES (p_passenger_id, p_flight_id, p_seat_number, 'CONFIRMED');

        SET p_reservation_id = LAST_INSERT_ID();

        -- 4. Insert Payment
        INSERT INTO Payments (Reservation_ID, Amount, Payment_Status)
        VALUES (p_reservation_id, p_total_amount, 'SUCCESS');

        COMMIT;
        SET p_status_msg = 'BOOKING_CONFIRMED: Reservation and payment recorded atomically.';
    END IF;
END$$

DELIMITER ;
