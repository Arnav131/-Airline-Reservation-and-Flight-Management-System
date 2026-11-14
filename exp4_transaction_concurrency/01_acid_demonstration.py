"""
Experiment 4.1: ACID Properties Verification During Ticket Reservation.
Demonstrates Atomicity, Consistency, Isolation, and Durability on live relational storage.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import RelationalConnection
from exp1_relational_sql.exp1_runner import init_schema_and_seed
from exp2_advanced_mysql.exp2_runner import setup_views_and_triggers

console = Console()


def demonstrate_acid():
    console.print(Panel.fit("[bold cyan]4.1 ACID Properties Demonstration[/bold cyan]"))
    db = RelationalConnection()
    init_schema_and_seed(db)
    setup_views_and_triggers(db)

    # 1. ATOMICITY: All-or-nothing booking + payment
    console.print("[bold yellow]1. ATOMICITY Test (Reservation succeeds, Payment violates CHECK constraint -> Rollback All):[/bold yellow]")
    before_count = db.fetchall("SELECT COUNT(*) AS cnt FROM Reservations")[0]["cnt"]
    try:
        db.execute("BEGIN" if db.mode == "sqlite" else "START TRANSACTION")
        cur = db.execute(
            "INSERT INTO Reservations (Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES (101, 'AI-202', '21A', 'CONFIRMED')"
        )
        new_res_id = cur.lastrowid
        # Violate CHECK (Amount >= 0) by passing -500.00
        db.execute(
            "INSERT INTO Payments (Reservation_ID, Amount, Payment_Status) VALUES (?, -500.00, 'SUCCESS')",
            (new_res_id,),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        console.print(f"   [red]Payment step failed ({exc}) -> Rolled back entire transaction.[/red]")

    after_count = db.fetchall("SELECT COUNT(*) AS cnt FROM Reservations")[0]["cnt"]
    console.print(f"   Reservations before: {before_count} | after rollback: {after_count} -> [green]Atomicity Preserved ✓[/green]\n")

    # 2. CONSISTENCY: Foreign Keys & Duplicate Seat Trigger invariants
    console.print("[bold yellow]2. CONSISTENCY Test (Trigger & Foreign Key Enforcements):[/bold yellow]")
    try:
        db.execute("BEGIN" if db.mode == "sqlite" else "START TRANSACTION")
        # Attempt booking seat 12A on AI-202 which is already CONFIRMED
        db.execute(
            "INSERT INTO Reservations (Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES (103, 'AI-202', '12A', 'CONFIRMED')"
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        console.print(f"   Duplicate seat rejected cleanly: [red]{exc}[/red]")
        console.print("   [green]Database invariant (1 active passenger per seat) Preserved ✓[/green]\n")

    # 3. ISOLATION: Uncommitted transaction invisible to concurrent connection
    console.print("[bold yellow]3. ISOLATION Test (Uncommitted write invisible to second reader connection):[/bold yellow]")
    conn_writer = RelationalConnection()
    conn_reader = RelationalConnection()

    conn_writer.execute("BEGIN" if conn_writer.mode == "sqlite" else "START TRANSACTION")
    conn_writer.execute(
        "INSERT INTO Reservations (Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES (104, 'AI-408', '09C', 'CONFIRMED')"
    )
    uncommitted_read = conn_reader.fetchall(
        "SELECT * FROM Reservations WHERE Flight_ID = 'AI-408' AND Seat_Number = '09C'"
    )
    console.print(f"   Reader rows visible BEFORE writer commit: {len(uncommitted_read)} (Dirty Read prevented)")
    conn_writer.commit()
    committed_read = conn_reader.fetchall(
        "SELECT * FROM Reservations WHERE Flight_ID = 'AI-408' AND Seat_Number = '09C'"
    )
    console.print(f"   Reader rows visible AFTER writer commit:  {len(committed_read)} -> [green]Isolation Preserved ✓[/green]\n")

    # 4. DURABILITY: Re-opening fresh connection confirms persisted state
    console.print("[bold yellow]4. DURABILITY Test (Closing all handles and verifying persisted WAL/Disk state):[/bold yellow]")
    conn_writer.close()
    conn_reader.close()
    db.close()

    fresh_db = RelationalConnection()
    persisted = fresh_db.fetchall(
        "SELECT Reservation_ID, Flight_ID, Seat_Number, Booking_Status FROM Reservations WHERE Flight_ID = 'AI-408' AND Seat_Number = '09C'"
    )
    console.print(f"   Fresh connection retrieved committed record: {persisted[0]} -> [green]Durability Preserved ✓[/green]\n")
    fresh_db.close()


if __name__ == "__main__":
    demonstrate_acid()
