-- ============================================================================
-- Experiment 1: Sample Seed Data (IARFMS)
-- ============================================================================

USE iarfms_db;

-- Airports (Domestic & International Hubs)
INSERT INTO Airports (Airport_ID, Airport_Name, City) VALUES
('DEL', 'Indira Gandhi International Airport', 'New Delhi'),
('BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'Mumbai'),
('BLR', 'Kempegowda International Airport', 'Bengaluru'),
('MAA', 'Chennai International Airport', 'Chennai'),
('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad'),
('DXB', 'Dubai International Airport', 'Dubai'),
('SIN', 'Singapore Changi Airport', 'Singapore'),
('LHR', 'London Heathrow Airport', 'London');

-- Aircraft Fleet
INSERT INTO Aircraft (Aircraft_ID, Aircraft_Model, Capacity) VALUES
(1, 'Airbus A320neo', 180),
(2, 'Boeing 737-800', 186),
(3, 'Boeing 787-9 Dreamliner', 290),
(4, 'Airbus A350-900', 325);

-- Passengers
INSERT INTO Passengers (Passenger_ID, Name, Email, Contact) VALUES
(101, 'Aarav Sharma',     'aarav.sharma@example.com',    '+91-9810011223'),
(102, 'Diya Patel',       'diya.patel@example.com',      '+91-9820022334'),
(103, 'Rohan Verma',      'rohan.verma@example.com',     '+91-9830033445'),
(104, 'Ananya Iyer',      'ananya.iyer@example.com',     '+91-9840044556'),
(105, 'Kabir Malhotra',   'kabir.malhotra@example.com',  '+91-9850055667'),
(106, 'Meera Nair',       'meera.nair@example.com',      '+91-9860066778'),
(107, 'Vikramaditya Rao', 'vikram.rao@example.com',      '+91-9870077889'),
(108, 'Sneha Kulkarni',   'sneha.kulkarni@example.com',  '+91-9880088990');

-- Flights
INSERT INTO Flights (Flight_ID, Source_Airport, Destination_Airport, Aircraft_ID, Departure_Time, Flight_Status, Base_Fare) VALUES
('AI-202', 'DEL', 'BOM', 1, '2026-11-12 08:30:00', 'ON_TIME',  5200.00),
('AI-304', 'BOM', 'BLR', 2, '2026-11-12 11:45:00', 'ON_TIME',  4100.00),
('AI-408', 'BLR', 'MAA', 1, '2026-11-12 15:15:00', 'ON_TIME',  3200.00),
('AI-510', 'DEL', 'DXB', 3, '2026-11-12 20:00:00', 'ON_TIME', 18500.00),
('AI-612', 'BOM', 'LHR', 4, '2026-11-13 02:15:00', 'ON_TIME', 46000.00),
('AI-715', 'DEL', 'BLR', 2, '2026-11-12 13:00:00', 'ON_TIME',  6100.00),
('AI-820', 'BLR', 'SIN', 3, '2026-11-13 00:30:00', 'ON_TIME', 22000.00),
('AI-905', 'HYD', 'DEL', 1, '2026-11-12 17:45:00', 'ON_TIME',  4800.00);

-- Reservations
INSERT INTO Reservations (Reservation_ID, Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES
(1001, 101, 'AI-202', '12A', 'CONFIRMED'),
(1002, 102, 'AI-202', '12B', 'CONFIRMED'),
(1003, 103, 'AI-304', '04C', 'CONFIRMED'),
(1004, 104, 'AI-510', '01A', 'CONFIRMED'),
(1005, 105, 'AI-612', '02F', 'PENDING'),
(1006, 106, 'AI-202', '14D', 'CANCELLED'),
(1007, 107, 'AI-715', '18A', 'CONFIRMED'),
(1008, 108, 'AI-820', '06K', 'CONFIRMED');

-- Payments
INSERT INTO Payments (Payment_ID, Reservation_ID, Amount, Payment_Status) VALUES
(5001, 1001,  5200.00, 'SUCCESS'),
(5002, 1002,  5200.00, 'SUCCESS'),
(5003, 1003,  4100.00, 'SUCCESS'),
(5004, 1004, 40700.00, 'SUCCESS'),
(5005, 1005, 46000.00, 'PENDING'),
(5006, 1006,  5200.00, 'REFUNDED'),
(5007, 1007,  6100.00, 'SUCCESS'),
(5008, 1008, 22000.00, 'SUCCESS');

-- Crew
INSERT INTO Crew (Crew_ID, Name, Designation) VALUES
(201, 'Capt. Rajesh Rathore',   'Captain'),
(202, 'FO Priya Deshmukh',      'First Officer'),
(203, 'Sonia Kapoor',           'Purser'),
(204, 'Arjun Menon',            'Flight Attendant'),
(205, 'Capt. Vikram Sethi',     'Captain'),
(206, 'FO Neha Joshi',          'First Officer');

-- Crew Assignments
INSERT INTO Crew_Assignments (Flight_ID, Crew_ID, Duty_Role) VALUES
('AI-202', 201, 'Pilot in Command'),
('AI-202', 202, 'Co-Pilot'),
('AI-202', 203, 'Lead Cabin Crew'),
('AI-202', 204, 'Cabin Safety'),
('AI-510', 205, 'Pilot in Command'),
('AI-510', 206, 'Co-Pilot');
