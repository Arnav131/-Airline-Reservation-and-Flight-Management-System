-- ============================================================================
-- Experiment 2.2: TRIGGER to Prevent Duplicate Seat Assignments (MySQL 8.0)
-- Note: Allows re-booking a seat ONLY if the previous booking was CANCELLED.
-- ============================================================================
USE iarfms_db;

DROP TRIGGER IF EXISTS trg_prevent_duplicate_seat;
DROP TRIGGER IF EXISTS trg_prevent_duplicate_seat_update;

DELIMITER $$

CREATE TRIGGER trg_prevent_duplicate_seat
BEFORE INSERT ON Reservations
FOR EACH ROW
BEGIN
    DECLARE v_seat_count INT DEFAULT 0;

    IF NEW.Booking_Status IN ('CONFIRMED', 'PENDING') THEN
        SELECT COUNT(*) INTO v_seat_count
        FROM Reservations
        WHERE Flight_ID = NEW.Flight_ID
          AND Seat_Number = NEW.Seat_Number
          AND Booking_Status IN ('CONFIRMED', 'PENDING');

        IF v_seat_count > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'DUPLICATE_SEAT_ERROR: Seat is already occupied on this flight.';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_prevent_duplicate_seat_update
BEFORE UPDATE ON Reservations
FOR EACH ROW
BEGIN
    DECLARE v_seat_count INT DEFAULT 0;

    IF NEW.Booking_Status IN ('CONFIRMED', 'PENDING')
       AND (OLD.Seat_Number <> NEW.Seat_Number OR OLD.Booking_Status <> NEW.Booking_Status) THEN
        SELECT COUNT(*) INTO v_seat_count
        FROM Reservations
        WHERE Flight_ID = NEW.Flight_ID
          AND Seat_Number = NEW.Seat_Number
          AND Booking_Status IN ('CONFIRMED', 'PENDING')
          AND Reservation_ID <> NEW.Reservation_ID;

        IF v_seat_count > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'DUPLICATE_SEAT_ERROR: Target seat is already occupied on this flight.';
        END IF;
    END IF;
END$$

DELIMITER ;
