-- ============================================================================
-- Experiment 2.3: FUNCTION to Calculate Dynamic Ticket Charges (MySQL 8.0)
-- Pricing Factors: Base Fare * Class Multiplier + Demand/Urgency Surge + 12% Tax
-- ============================================================================
USE iarfms_db;

DROP FUNCTION IF EXISTS fn_calculate_ticket_charge;

DELIMITER $$

CREATE FUNCTION fn_calculate_ticket_charge(
    p_flight_id VARCHAR(15),
    p_seat_class VARCHAR(20),
    p_days_before_departure INT
) RETURNS DECIMAL(10, 2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_base_fare DECIMAL(10, 2) DEFAULT 4500.00;
    DECLARE v_class_multiplier DECIMAL(5, 2) DEFAULT 1.00;
    DECLARE v_urgency_surge DECIMAL(5, 2) DEFAULT 1.00;
    DECLARE v_subtotal DECIMAL(10, 2);
    DECLARE v_tax_rate DECIMAL(4, 2) DEFAULT 0.12; -- 12% GST

    SELECT Base_Fare INTO v_base_fare
    FROM Flights
    WHERE Flight_ID = p_flight_id
    LIMIT 1;

    -- Seat Class Multiplier
    IF UPPER(p_seat_class) = 'FIRST' THEN
        SET v_class_multiplier = 3.20;
    ELSEIF UPPER(p_seat_class) = 'BUSINESS' THEN
        SET v_class_multiplier = 2.10;
    ELSE
        SET v_class_multiplier = 1.00; -- ECONOMY
    END IF;

    -- Last-minute booking surge (< 3 days before departure adds 25%, < 7 days adds 10%)
    IF p_days_before_departure <= 3 THEN
        SET v_urgency_surge = 1.25;
    ELSEIF p_days_before_departure <= 7 THEN
        SET v_urgency_surge = 1.10;
    END IF;

    SET v_subtotal = v_base_fare * v_class_multiplier * v_urgency_surge;
    RETURN ROUND(v_subtotal * (1 + v_tax_rate), 2);
END$$

DELIMITER ;

-- Example call:
-- SELECT Flight_ID, fn_calculate_ticket_charge(Flight_ID, 'BUSINESS', 2) AS Business_Urgent_Fare FROM Flights;
