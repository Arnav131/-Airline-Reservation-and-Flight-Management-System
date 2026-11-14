"""
Experiment 2 Runner: Advanced MySQL Programming (View, Trigger, Stored Proc, Function, Cursor).
Demonstrates live execution across MySQL 8.0 or SQLite+Python Dual-Engine.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import RelationalConnection, render_table
from exp1_relational_sql.exp1_runner import init_schema_and_seed

console = Console()


def fn_calculate_ticket_charge(db: RelationalConnection, flight_id: str, seat_class: str, days_before_dep: int) -> float:
    """Equivalent to MySQL fn_calculate_ticket_charge(flight_id, seat_class, days_before_dep)."""
    if db.mode == "mysql":
        row = db.fetchall("SELECT fn_calculate_ticket_charge(%s, %s, %s) AS amt", (flight_id, seat_class, days_before_dep))
        return float(row[0]["amt"])

    row = db.fetchall("SELECT Base_Fare FROM Flights WHERE Flight_ID = ?", (flight_id,))
    base_fare = float(row[0]["Base_Fare"]) if row else 4500.0
    mult = {"FIRST": 3.20, "BUSINESS": 2.10}.get(seat_class.upper(), 1.00)
    surge = 1.25 if days_before_dep <= 3 else (1.10 if days_before_dep <= 7 else 1.00)
    return round(base_fare * mult * surge * 1.12, 2)


def sp_book_flight_ticket(
    db: RelationalConnection, passenger_id: int, flight_id: str, seat_number: str, seat_class: str = "ECONOMY"
) -> tuple[bool, int, float, str]:
    """Atomic ticket booking procedure matching sp_book_flight_ticket."""
    try:
        db.execute("BEGIN" if db.mode == "sqlite" else "START TRANSACTION")
        cap_rows = db.fetchall(
            "SELECT a.Capacity FROM Flights f JOIN Aircraft a ON f.Aircraft_ID = a.Aircraft_ID WHERE f.Flight_ID = ?",
            (flight_id,),
        )
        if not cap_rows:
            db.rollback()
            return False, -1, 0.0, f"BOOKING_FAILED: Unknown Flight {flight_id}"

        capacity = cap_rows[0]["Capacity"]
        booked = db.fetchall(
            "SELECT COUNT(*) AS cnt FROM Reservations WHERE Flight_ID = ? AND Booking_Status = 'CONFIRMED'",
            (flight_id,),
        )[0]["cnt"]
        if booked >= capacity:
            db.rollback()
            return False, -1, 0.0, "BOOKING_FAILED: Aircraft capacity full."

        total_amount = fn_calculate_ticket_charge(db, flight_id, seat_class, days_before_dep=2)

        cur = db.execute(
            "INSERT INTO Reservations (Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES (?, ?, ?, 'CONFIRMED')",
            (passenger_id, flight_id, seat_number),
        )
        res_id = cur.lastrowid
        db.execute(
            "INSERT INTO Payments (Reservation_ID, Amount, Payment_Status) VALUES (?, ?, 'SUCCESS')",
            (res_id, total_amount),
        )
        db.commit()
        return True, res_id, total_amount, "BOOKING_CONFIRMED: Reservation & Payment committed atomically."
    except Exception as exc:
        db.rollback()
        return False, -1, 0.0, f"BOOKING_FAILED (Rolled Back): {exc}"


def sp_generate_flight_passenger_manifest(db: RelationalConnection, flight_id: str) -> list[dict]:
    """Cursor-based manifest generation matching sp_generate_flight_passenger_manifest."""
    cur = db.execute(
        """
        SELECT r.Reservation_ID, p.Name AS Passenger_Name, r.Seat_Number, r.Booking_Status
        FROM Reservations r
        INNER JOIN Passengers p ON r.Passenger_ID = p.Passenger_ID
        WHERE r.Flight_ID = ? AND r.Booking_Status = 'CONFIRMED'
        ORDER BY r.Seat_Number ASC
        """,
        (flight_id,),
    )
    manifest = []
    seq = 1
    while True:
        row = cur.fetchone()
        if row is None:
            break
        r_dict = dict(row) if db.mode == "sqlite" else {
            "Reservation_ID": row[0],
            "Passenger_Name": row[1],
            "Seat_Number": row[2],
            "Booking_Status": row[3],
        }
        manifest.append(
            {
                "Seq_No": seq,
                "Flight_ID": flight_id,
                "Reservation_ID": r_dict["Reservation_ID"],
                "Passenger_Name": r_dict["Passenger_Name"],
                "Seat_Number": r_dict["Seat_Number"],
                "Boarding_Pass_Code": f"BP-{flight_id}-{r_dict['Seat_Number']}-{r_dict['Reservation_ID']}",
            }
        )
        seq += 1
    return manifest


def setup_views_and_triggers(db: RelationalConnection) -> None:
    """Install VIEW v_passenger_reservations and TRIGGER trg_prevent_duplicate_seat."""
    if db.mode == "sqlite":
        db.execute("DROP VIEW IF EXISTS v_passenger_reservations;")
        db.execute(
            """
            CREATE VIEW v_passenger_reservations AS
            SELECT
                r.Reservation_ID, p.Passenger_ID, p.Name AS Passenger_Name, p.Email AS Passenger_Email,
                f.Flight_ID, src.Airport_ID AS Origin_Code, src.City AS Origin_City,
                dst.Airport_ID AS Dest_Code, dst.City AS Dest_City, a.Aircraft_Model,
                f.Departure_Time, f.Flight_Status, r.Seat_Number, r.Booking_Status,
                COALESCE(pay.Amount, 0.00) AS Ticket_Amount,
                COALESCE(pay.Payment_Status, 'UNPAID') AS Payment_Status
            FROM Reservations r
            INNER JOIN Passengers p ON r.Passenger_ID = p.Passenger_ID
            INNER JOIN Flights f    ON r.Flight_ID    = f.Flight_ID
            INNER JOIN Airports src ON f.Source_Airport = src.Airport_ID
            INNER JOIN Airports dst ON f.Destination_Airport = dst.Airport_ID
            INNER JOIN Aircraft a   ON f.Aircraft_ID  = a.Aircraft_ID
            LEFT JOIN  Payments pay ON r.Reservation_ID = pay.Reservation_ID;
            """
        )
        db.execute("DROP TRIGGER IF EXISTS trg_prevent_duplicate_seat;")
        db.execute(
            """
            CREATE TRIGGER trg_prevent_duplicate_seat
            BEFORE INSERT ON Reservations
            FOR EACH ROW
            WHEN NEW.Booking_Status IN ('CONFIRMED', 'PENDING')
            BEGIN
                SELECT RAISE(ABORT, 'DUPLICATE_SEAT_ERROR: Seat is already occupied on this flight.')
                WHERE EXISTS (
                    SELECT 1 FROM Reservations
                    WHERE Flight_ID = NEW.Flight_ID
                      AND Seat_Number = NEW.Seat_Number
                      AND Booking_Status IN ('CONFIRMED', 'PENDING')
                );
            END;
            """
        )
        db.commit()


def run_experiment_2():
    console.print(Panel.fit("[bold green]EXPERIMENT 2: Advanced MySQL Programming (View, Trigger, Proc, Func, Cursor)[/bold green]"))
    db = RelationalConnection()
    init_schema_and_seed(db)
    setup_views_and_triggers(db)

    # 1. Query VIEW
    view_rows = db.fetchall("SELECT Reservation_ID, Passenger_Name, Flight_ID, Origin_Code, Dest_Code, Seat_Number, Ticket_Amount FROM v_passenger_reservations WHERE Booking_Status = 'CONFIRMED'")
    render_table("1. VIEW (v_passenger_reservations) Output", view_rows)

    # 2. FUNCTION: Dynamic Pricing Breakdown
    pricing_rows = []
    for fid in ["AI-202", "AI-510", "AI-612"]:
        pricing_rows.append(
            {
                "Flight_ID": fid,
                "Economy (10d advance)": fn_calculate_ticket_charge(db, fid, "ECONOMY", 10),
                "Business (5d advance)": fn_calculate_ticket_charge(db, fid, "BUSINESS", 5),
                "First Class (Urgent 2d)": fn_calculate_ticket_charge(db, fid, "FIRST", 2),
            }
        )
    render_table("2. FUNCTION (fn_calculate_ticket_charge) Pricing Matrix (incl. 12% GST)", pricing_rows)

    # 3. PROCEDURE: Valid Ticket Booking
    console.print("\n[bold cyan]3. Testing Stored Procedure (sp_book_flight_ticket) — Valid Seat 15C on AI-202:[/bold cyan]")
    ok, res_id, amt, msg = sp_book_flight_ticket(db, passenger_id=103, flight_id="AI-202", seat_number="15C", seat_class="BUSINESS")
    console.print(f"   Status: [green]{msg}[/green] | Reservation_ID: [bold]{res_id}[/bold] | Charged: [bold]₹{amt}[/bold]")

    # 4. TRIGGER: Duplicate Seat Guard Check
    console.print("\n[bold cyan]4. Testing Trigger (trg_prevent_duplicate_seat) — Attempting Duplicate Booking on Seat 12A (AI-202):[/bold cyan]")
    ok2, res_id2, amt2, msg2 = sp_book_flight_ticket(db, passenger_id=105, flight_id="AI-202", seat_number="12A", seat_class="ECONOMY")
    console.print(f"   Expected Guard Interception -> [red]{msg2}[/red]")

    # 5. Re-booking a CANCELLED seat (14D on AI-202 was CANCELLED in seed data)
    console.print("\n[bold cyan]5. Testing Re-Booking Cancelled Seat 14D on AI-202 (Allowed by Conditional Trigger):[/bold cyan]")
    ok3, res_id3, amt3, msg3 = sp_book_flight_ticket(db, passenger_id=108, flight_id="AI-202", seat_number="14D", seat_class="ECONOMY")
    console.print(f"   Status: [green]{msg3}[/green] | Reservation_ID: [bold]{res_id3}[/bold]\n")

    # 6. CURSOR: Flight-wise Passenger Manifest
    manifest = sp_generate_flight_passenger_manifest(db, "AI-202")
    render_table("6. CURSOR (sp_generate_flight_passenger_manifest) for Flight AI-202", manifest)

    db.close()


if __name__ == "__main__":
    run_experiment_2()
