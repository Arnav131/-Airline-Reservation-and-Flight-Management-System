-- ============================================================================
-- Experiment 1: Relational Database Schema (MySQL 8.0 Dialect)
-- Project: Integrated Airline Reservation and Flight Management System (IARFMS)
-- Normalization: Verified up to BCNF (No partial or transitive dependencies)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS iarfms_db;
USE iarfms_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS Crew_Assignments;
DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Reservations;
DROP TABLE IF EXISTS Flights;
DROP TABLE IF EXISTS Crew;
DROP TABLE IF EXISTS Aircraft;
DROP TABLE IF EXISTS Airports;
DROP TABLE IF EXISTS Passengers;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Passengers Table
CREATE TABLE Passengers (
    Passenger_ID INT PRIMARY KEY AUTO_INCREMENT,
    Name         VARCHAR(100) NOT NULL,
    Email        VARCHAR(120) NOT NULL UNIQUE,
    Contact      VARCHAR(20)  NOT NULL
) ENGINE=InnoDB;

-- 2. Airports Table
CREATE TABLE Airports (
    Airport_ID   VARCHAR(10)  PRIMARY KEY, -- IATA Code e.g., DEL, BOM, BLR
    Airport_Name VARCHAR(150) NOT NULL,
    City         VARCHAR(80)  NOT NULL
) ENGINE=InnoDB;

-- 3. Aircraft Table
CREATE TABLE Aircraft (
    Aircraft_ID    INT PRIMARY KEY AUTO_INCREMENT,
    Aircraft_Model VARCHAR(80) NOT NULL,
    Capacity       INT NOT NULL,
    CONSTRAINT chk_aircraft_capacity CHECK (Capacity > 0 AND Capacity <= 850)
) ENGINE=InnoDB;

-- 4. Flights Table
CREATE TABLE Flights (
    Flight_ID           VARCHAR(15) PRIMARY KEY, -- e.g., AI-202
    Source_Airport      VARCHAR(10) NOT NULL,
    Destination_Airport VARCHAR(10) NOT NULL,
    Aircraft_ID         INT         NOT NULL,
    Departure_Time      DATETIME    NOT NULL,
    Flight_Status       VARCHAR(30) NOT NULL DEFAULT 'ON_TIME',
    Base_Fare           DECIMAL(10,2) NOT NULL DEFAULT 4500.00,
    CONSTRAINT fk_flight_src FOREIGN KEY (Source_Airport) REFERENCES Airports(Airport_ID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_flight_dst FOREIGN KEY (Destination_Airport) REFERENCES Airports(Airport_ID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_flight_aircraft FOREIGN KEY (Aircraft_ID) REFERENCES Aircraft(Aircraft_ID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_distinct_airports CHECK (Source_Airport <> Destination_Airport)
) ENGINE=InnoDB;

-- 5. Reservations Table
CREATE TABLE Reservations (
    Reservation_ID INT PRIMARY KEY AUTO_INCREMENT,
    Passenger_ID   INT         NOT NULL,
    Flight_ID      VARCHAR(15) NOT NULL,
    Seat_Number    VARCHAR(10) NOT NULL,
    Booking_Status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    Booked_At      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_res_passenger FOREIGN KEY (Passenger_ID) REFERENCES Passengers(Passenger_ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_res_flight FOREIGN KEY (Flight_ID) REFERENCES Flights(Flight_ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_booking_status CHECK (Booking_Status IN ('CONFIRMED', 'PENDING', 'CANCELLED', 'WAITLIST'))
) ENGINE=InnoDB;

-- 6. Payments Table
CREATE TABLE Payments (
    Payment_ID     INT PRIMARY KEY AUTO_INCREMENT,
    Reservation_ID INT            NOT NULL,
    Amount         DECIMAL(10, 2) NOT NULL,
    Payment_Status VARCHAR(20)    NOT NULL DEFAULT 'PENDING',
    Paid_At        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pay_reservation FOREIGN KEY (Reservation_ID) REFERENCES Reservations(Reservation_ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_payment_amount CHECK (Amount >= 0),
    CONSTRAINT chk_payment_status CHECK (Payment_Status IN ('SUCCESS', 'FAILED', 'PENDING', 'REFUNDED'))
) ENGINE=InnoDB;

-- 7. Crew Table
CREATE TABLE Crew (
    Crew_ID     INT PRIMARY KEY AUTO_INCREMENT,
    Name        VARCHAR(100) NOT NULL,
    Designation VARCHAR(60)  NOT NULL,
    CONSTRAINT chk_crew_designation CHECK (Designation IN ('Captain', 'First Officer', 'Purser', 'Flight Attendant', 'Flight Engineer'))
) ENGINE=InnoDB;

-- Supporting Associative Table for Flight Crew Assignments (M:N relationship)
CREATE TABLE Crew_Assignments (
    Assignment_ID INT PRIMARY KEY AUTO_INCREMENT,
    Flight_ID     VARCHAR(15) NOT NULL,
    Crew_ID       INT         NOT NULL,
    Duty_Role     VARCHAR(50) NOT NULL,
    UNIQUE KEY uk_flight_crew (Flight_ID, Crew_ID),
    CONSTRAINT fk_ca_flight FOREIGN KEY (Flight_ID) REFERENCES Flights(Flight_ID) ON DELETE CASCADE,
    CONSTRAINT fk_ca_crew   FOREIGN KEY (Crew_ID)   REFERENCES Crew(Crew_ID)   ON DELETE CASCADE
) ENGINE=InnoDB;
