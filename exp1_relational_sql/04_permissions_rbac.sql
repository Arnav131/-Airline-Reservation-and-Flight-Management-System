-- ============================================================================
-- Experiment 1: Role-Based Access Control (DCL: GRANT, REVOKE, ROLES)
-- ============================================================================

USE iarfms_db;

-- 1. Create Principle-of-Least-Privilege Roles
CREATE ROLE IF NOT EXISTS 'airline_admin_role', 'booking_agent_role', 'passenger_read_role';

-- 2. Grant Privileges to Roles
-- Admin gets full control over schema and data
GRANT ALL PRIVILEGES ON iarfms_db.* TO 'airline_admin_role';

-- Booking agent can inspect schedules and manage bookings/payments, but CANNOT drop tables or modify aircraft
GRANT SELECT ON iarfms_db.Flights      TO 'booking_agent_role';
GRANT SELECT ON iarfms_db.Airports     TO 'booking_agent_role';
GRANT SELECT ON iarfms_db.Aircraft     TO 'booking_agent_role';
GRANT SELECT, INSERT, UPDATE ON iarfms_db.Passengers   TO 'booking_agent_role';
GRANT SELECT, INSERT, UPDATE ON iarfms_db.Reservations TO 'booking_agent_role';
GRANT SELECT, INSERT, UPDATE ON iarfms_db.Payments     TO 'booking_agent_role';

-- Passenger gets read-only access to public flight data
GRANT SELECT ON iarfms_db.Flights  TO 'passenger_read_role';
GRANT SELECT ON iarfms_db.Airports TO 'passenger_read_role';

-- 3. Create Sample Users and Assign Roles
CREATE USER IF NOT EXISTS 'admin_ops'@'%'   IDENTIFIED BY 'AdminPass#2026';
CREATE USER IF NOT EXISTS 'agent_desk'@'%'  IDENTIFIED BY 'AgentPass#2026';
CREATE USER IF NOT EXISTS 'guest_flyer'@'%' IDENTIFIED BY 'FlyerPass#2026';

GRANT 'airline_admin_role'  TO 'admin_ops'@'%';
GRANT 'booking_agent_role'  TO 'agent_desk'@'%';
GRANT 'passenger_read_role' TO 'guest_flyer'@'%';

SET DEFAULT ROLE ALL TO 'admin_ops'@'%', 'agent_desk'@'%', 'guest_flyer'@'%';

-- 4. Demonstrate REVOKE (e.g., revoking UPDATE on Payments from booking agents for audit security)
REVOKE UPDATE ON iarfms_db.Payments FROM 'booking_agent_role';

-- Verify active grants
SHOW GRANTS FOR 'booking_agent_role';
