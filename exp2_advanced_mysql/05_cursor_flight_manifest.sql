-- ============================================================================
-- Experiment 2.5: CURSOR to Generate Flight-Wise Passenger Manifest Lists
-- ============================================================================
USE iarfms_db;

DROP PROCEDURE IF EXISTS sp_generate_flight_passenger_manifest;

DELIMITER $$

CREATE PROCEDURE sp_generate_flight_passenger_manifest(IN p_flight_id VARCHAR(15))
BEGIN
    DECLARE v_done INT DEFAULT FALSE;
    DECLARE v_res_id INT;
    DECLARE v_name VARCHAR(100);
    DECLARE v_seat VARCHAR(10);
    DECLARE v_status VARCHAR(20);

    -- Cursor over confirmed/pending passengers on a specific flight
    DECLARE cur_manifest CURSOR FOR
        SELECT r.Reservation_ID, p.Name, r.Seat_Number, r.Booking_Status
        FROM Reservations r
        INNER JOIN Passengers p ON r.Passenger_ID = p.Passenger_ID
        WHERE r.Flight_ID = p_flight_id
          AND r.Booking_Status = 'CONFIRMED'
        ORDER BY r.Seat_Number ASC;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;

    -- Temporary staging table to output formatted manifest rows cleanly
    DROP TEMPORARY TABLE IF EXISTS tmp_flight_manifest;
    CREATE TEMPORARY TABLE tmp_flight_manifest (
        Seq_No         INT AUTO_INCREMENT PRIMARY KEY,
        Flight_ID      VARCHAR(15),
        Reservation_ID INT,
        Passenger_Name VARCHAR(100),
        Seat_Number    VARCHAR(10),
        Boarding_Pass_Code VARCHAR(60)
    );

    OPEN cur_manifest;

    manifest_loop: LOOP
        FETCH cur_manifest INTO v_res_id, v_name, v_seat, v_status;
        IF v_done THEN
            LEAVE manifest_loop;
        END IF;

        INSERT INTO tmp_flight_manifest (Flight_ID, Reservation_ID, Passenger_Name, Seat_Number, Boarding_Pass_Code)
        VALUES (
            p_flight_id,
            v_res_id,
            v_name,
            v_seat,
            CONCAT('BP-', p_flight_id, '-', v_seat, '-', v_res_id)
        );
    END LOOP;

    CLOSE cur_manifest;

    SELECT * FROM tmp_flight_manifest;
END$$

DELIMITER ;
