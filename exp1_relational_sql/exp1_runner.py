"""
Experiment 1 Runner: Relational Database Schema, Joins, RBAC & Transaction Control.
Executes natively on MySQL 8.0 (if running) or seamlessly on embedded SQLite WAL engine.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import RelationalConnection, render_table

console = Console()


def _split_sql_statements(raw_sql: str) -> list[str]:
    """Strip SQL line comments and split into executable statements."""
    cleaned_lines = [
        line for line in raw_sql.splitlines() if not line.strip().startswith("--")
    ]
    cleaned_sql = "\n".join(cleaned_lines)
    stmts = []
    for stmt in cleaned_sql.split(";"):
        s = stmt.strip()
        if s and not s.upper().startswith(("USE ", "CREATE DATABASE")):
            stmts.append(s)
    return stmts


def init_schema_and_seed(db: RelationalConnection) -> None:
    """Create the 7 core IARFMS relational tables (+ Crew_Assignments) and seed data."""
    if db.mode == "sqlite":
        ddl_statements = [
            "PRAGMA foreign_keys = OFF;",
            "DROP TABLE IF EXISTS Crew_Assignments;",
            "DROP TABLE IF EXISTS Payments;",
            "DROP TABLE IF EXISTS Reservations;",
            "DROP TABLE IF EXISTS Flights;",
            "DROP TABLE IF EXISTS Crew;",
            "DROP TABLE IF EXISTS Aircraft;",
            "DROP TABLE IF EXISTS Airports;",
            "DROP TABLE IF EXISTS Passengers;",
            "PRAGMA foreign_keys = ON;",
            """
            CREATE TABLE Passengers (
                Passenger_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name         TEXT NOT NULL,
                Email        TEXT NOT NULL UNIQUE,
                Contact      TEXT NOT NULL
            );""",
            """
            CREATE TABLE Airports (
                Airport_ID   TEXT PRIMARY KEY,
                Airport_Name TEXT NOT NULL,
                City         TEXT NOT NULL
            );""",
            """
            CREATE TABLE Aircraft (
                Aircraft_ID    INTEGER PRIMARY KEY AUTOINCREMENT,
                Aircraft_Model TEXT NOT NULL,
                Capacity       INTEGER NOT NULL CHECK (Capacity > 0 AND Capacity <= 850)
            );""",
            """
            CREATE TABLE Flights (
                Flight_ID           TEXT PRIMARY KEY,
                Source_Airport      TEXT NOT NULL REFERENCES Airports(Airport_ID) ON UPDATE CASCADE ON DELETE RESTRICT,
                Destination_Airport TEXT NOT NULL REFERENCES Airports(Airport_ID) ON UPDATE CASCADE ON DELETE RESTRICT,
                Aircraft_ID         INTEGER NOT NULL REFERENCES Aircraft(Aircraft_ID) ON UPDATE CASCADE ON DELETE RESTRICT,
                Departure_Time      TEXT NOT NULL,
                Flight_Status       TEXT NOT NULL DEFAULT 'ON_TIME',
                Base_Fare           REAL NOT NULL DEFAULT 4500.00,
                CHECK (Source_Airport <> Destination_Airport)
            );""",
            """
            CREATE TABLE Reservations (
                Reservation_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Passenger_ID   INTEGER NOT NULL REFERENCES Passengers(Passenger_ID) ON UPDATE CASCADE ON DELETE CASCADE,
                Flight_ID      TEXT NOT NULL REFERENCES Flights(Flight_ID) ON UPDATE CASCADE ON DELETE CASCADE,
                Seat_Number    TEXT NOT NULL,
                Booking_Status TEXT NOT NULL DEFAULT 'PENDING' CHECK (Booking_Status IN ('CONFIRMED', 'PENDING', 'CANCELLED', 'WAITLIST')),
                Booked_At      TEXT NOT NULL DEFAULT (datetime('now'))
            );""",
            """
            CREATE TABLE Payments (
                Payment_ID     INTEGER PRIMARY KEY AUTOINCREMENT,
                Reservation_ID INTEGER NOT NULL REFERENCES Reservations(Reservation_ID) ON UPDATE CASCADE ON DELETE CASCADE,
                Amount         REAL NOT NULL CHECK (Amount >= 0),
                Payment_Status TEXT NOT NULL DEFAULT 'PENDING' CHECK (Payment_Status IN ('SUCCESS', 'FAILED', 'PENDING', 'REFUNDED')),
                Paid_At        TEXT NOT NULL DEFAULT (datetime('now'))
            );""",
            """
            CREATE TABLE Crew (
                Crew_ID     INTEGER PRIMARY KEY AUTOINCREMENT,
                Name        TEXT NOT NULL,
                Designation TEXT NOT NULL CHECK (Designation IN ('Captain', 'First Officer', 'Purser', 'Flight Attendant', 'Flight Engineer'))
            );""",
            """
            CREATE TABLE Crew_Assignments (
                Assignment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Flight_ID     TEXT NOT NULL REFERENCES Flights(Flight_ID) ON DELETE CASCADE,
                Crew_ID       INTEGER NOT NULL REFERENCES Crew(Crew_ID) ON DELETE CASCADE,
                Duty_Role     TEXT NOT NULL,
                UNIQUE (Flight_ID, Crew_ID)
            );""",
        ]
        for stmt in ddl_statements:
            db.execute(stmt)
    else:
        ddl_path = Path(__file__).parent / "01_schema_ddl.sql"
        for s in _split_sql_statements(ddl_path.read_text(encoding="utf-8")):
            db.execute(s)

    seed_path = Path(__file__).parent / "02_sample_data.sql"
    db.execute("BEGIN" if db.mode == "sqlite" else "START TRANSACTION")
    for s in _split_sql_statements(seed_path.read_text(encoding="utf-8")):
        db.execute(s)
    db.commit()


def run_experiment_1():
    console.print(Panel.fit("[bold green]EXPERIMENT 1: Relational Database using SQL (IARFMS)[/bold green]"))
    db = RelationalConnection()
    console.print(f"[cyan]Active Relational Engine Mode:[/cyan] [bold]{db.mode.upper()}[/bold]")

    init_schema_and_seed(db)
    console.print("[green]✓ 7 Core Tables + Crew_Assignments initialized and seeded successfully.[/green]\n")

    # 1. Multi-table JOIN Query
    itinerary_sql = """
    SELECT
        r.Reservation_ID,
        p.Name AS Passenger_Name,
        f.Flight_ID,
        src.City || ' (' || src.Airport_ID || ')' AS Origin,
        dst.City || ' (' || dst.Airport_ID || ')' AS Destination,
        a.Aircraft_Model,
        r.Seat_Number,
        r.Booking_Status,
        COALESCE(pay.Amount, 0.0) AS Amount,
        COALESCE(pay.Payment_Status, 'UNPAID') AS Payment_Status
    FROM Reservations r
    INNER JOIN Passengers p ON r.Passenger_ID = p.Passenger_ID
    INNER JOIN Flights f    ON r.Flight_ID    = f.Flight_ID
    INNER JOIN Airports src ON f.Source_Airport = src.Airport_ID
    INNER JOIN Airports dst ON f.Destination_Airport = dst.Airport_ID
    INNER JOIN Aircraft a   ON f.Aircraft_ID  = a.Aircraft_ID
    LEFT JOIN  Payments pay ON r.Reservation_ID = pay.Reservation_ID
    ORDER BY f.Departure_Time ASC, r.Reservation_ID ASC;
    """
    if db.mode == "mysql":
        itinerary_sql = itinerary_sql.replace("src.City || ' (' || src.Airport_ID || ')'", "CONCAT(src.City, ' (', src.Airport_ID, ')')")
        itinerary_sql = itinerary_sql.replace("dst.City || ' (' || dst.Airport_ID || ')'", "CONCAT(dst.City, ' (', dst.Airport_ID, ')')")

    rows = db.fetchall(itinerary_sql)
    render_table("1. Multi-Table JOIN: Passenger Flight & Payment Itinerary", rows)

    # 2. Available Seats Query
    avail_sql = """
    SELECT
        f.Flight_ID,
        f.Source_Airport AS From_Hub,
        f.Destination_Airport AS To_Hub,
        a.Aircraft_Model,
        a.Capacity,
        COUNT(CASE WHEN r.Booking_Status = 'CONFIRMED' THEN 1 END) AS Booked_Seats,
        (a.Capacity - COUNT(CASE WHEN r.Booking_Status = 'CONFIRMED' THEN 1 END)) AS Available_Seats,
        ROUND((CAST(COUNT(CASE WHEN r.Booking_Status = 'CONFIRMED' THEN 1 END) AS FLOAT) / a.Capacity) * 100, 2) AS Occupancy_Pct
    FROM Flights f
    INNER JOIN Aircraft a ON f.Aircraft_ID = a.Aircraft_ID
    LEFT JOIN Reservations r ON f.Flight_ID = r.Flight_ID
    GROUP BY f.Flight_ID, f.Source_Airport, f.Destination_Airport, a.Aircraft_Model, a.Capacity
    ORDER BY Booked_Seats DESC, f.Flight_ID ASC;
    """
    avail_rows = db.fetchall(avail_sql)
    render_table("2. Seat Availability & Occupancy Analytics", avail_rows)

    # 3. Crew Roster
    crew_sql = """
    SELECT f.Flight_ID, c.Name AS Crew_Member, c.Designation, ca.Duty_Role
    FROM Flights f
    JOIN Crew_Assignments ca ON f.Flight_ID = ca.Flight_ID
    JOIN Crew c ON ca.Crew_ID = c.Crew_ID
    ORDER BY f.Flight_ID;
    """
    render_table("3. Flight Crew Roster", db.fetchall(crew_sql))

    # 4. TCL Savepoint & Rollback Demonstration
    console.print("\n[bold cyan]4. Demonstrating Transaction Control (TCL: SAVEPOINT / ROLLBACK / COMMIT)...[/bold cyan]")
    db.execute("BEGIN" if db.mode == "sqlite" else "START TRANSACTION")
    db.execute(
        "INSERT INTO Reservations (Reservation_ID, Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES (1009, 101, 'AI-304', '07A', 'PENDING')"
    )
    db.execute("SAVEPOINT sp_res")
    db.execute(
        "INSERT INTO Payments (Payment_ID, Reservation_ID, Amount, Payment_Status) VALUES (5009, 1009, 4100.00, 'FAILED')"
    )
    console.print("   [yellow]→ Simulated payment failure (Payment 5009 FAILED). Rolling back to SAVEPOINT sp_res...[/yellow]")
    db.execute("ROLLBACK TO SAVEPOINT sp_res")
    db.execute(
        "INSERT INTO Payments (Payment_ID, Reservation_ID, Amount, Payment_Status) VALUES (5010, 1009, 4100.00, 'SUCCESS')"
    )
    db.execute("UPDATE Reservations SET Booking_Status = 'CONFIRMED' WHERE Reservation_ID = 1009")
    db.commit()

    tcl_check = db.fetchall(
        "SELECT r.Reservation_ID, r.Flight_ID, r.Seat_Number, r.Booking_Status, p.Payment_ID, p.Payment_Status "
        "FROM Reservations r JOIN Payments p ON r.Reservation_ID = p.Reservation_ID WHERE r.Reservation_ID = 1009"
    )
    render_table("TCL Verified Committed Record (Failed Payment 5009 Rolled Back, 5010 Committed)", tcl_check)

    # 5. RBAC Summary Display
    console.print("[bold cyan]5. RBAC DCL Policy (04_permissions_rbac.sql):[/bold cyan]")
    console.print("   • [green]airline_admin_role[/green]: ALL PRIVILEGES on iarfms_db.*")
    console.print("   • [yellow]booking_agent_role[/yellow]: SELECT Flights/Airports/Aircraft; SELECT/INSERT/UPDATE Reservations & Passengers (UPDATE on Payments REVOKED)")
    console.print("   • [blue]passenger_read_role[/blue]: SELECT Flights & Airports (Read-Only)\n")

    db.close()


if __name__ == "__main__":
    run_experiment_1()
