"""
Experiment 4.5: MVCC (Multi-Version Concurrency Control) Investigation.
Demonstrates non-blocking Snapshot Isolation during concurrent flight searches & booking updates:
  - Reader-A starts a consistent snapshot read (sees initial flight fare/status & seat count).
  - Writer-B updates flight fare and inserts a new reservation, then commits.
  - Reader-A reads again inside the SAME transaction: sees the exact pre-update snapshot (No Phantom/Non-Repeatable Read, Readers don't block Writers!).
  - Reader-C opens a fresh transaction AFTER commit: sees the new committed version.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import RelationalConnection, render_table
from exp1_relational_sql.exp1_runner import init_schema_and_seed

console = Console()


def demonstrate_mvcc():
    console.print(Panel.fit("[bold cyan]4.5 MVCC (Multi-Version Concurrency Control) Investigation[/bold cyan]"))
    init_db = RelationalConnection()
    init_schema_and_seed(init_db)
    init_db.close()

    # Open 3 independent connections
    reader_snapshot = RelationalConnection()
    writer_txn = RelationalConnection()
    reader_fresh = RelationalConnection()

    timeline = []

    # Step 1: Reader-A starts a read transaction (creates Read View / WAL Snapshot)
    reader_snapshot.execute("BEGIN" if reader_snapshot.mode == "sqlite" else "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; START TRANSACTION")
    snap_1 = reader_snapshot.fetchall(
        "SELECT f.Flight_ID, f.Flight_Status, f.Base_Fare, COUNT(r.Reservation_ID) AS Total_Res "
        "FROM Flights f LEFT JOIN Reservations r ON f.Flight_ID = r.Flight_ID "
        "WHERE f.Flight_ID = 'AI-202' GROUP BY f.Flight_ID"
    )[0]
    timeline.append({
        "Step": "1. Reader-A Opens Snapshot",
        "Connection": "Reader-A (Open Txn)",
        "Flight_Status": snap_1["Flight_Status"],
        "Base_Fare": snap_1["Base_Fare"],
        "Res_Count": snap_1["Total_Res"],
        "MVCC Observation": "Read View created at T0; sees initial version",
    })

    # Step 2: Writer-B modifies Flights and adds a Reservation concurrently WITHOUT waiting for Reader-A!
    writer_txn.execute("BEGIN IMMEDIATE" if writer_txn.mode == "sqlite" else "START TRANSACTION")
    writer_txn.execute("UPDATE Flights SET Flight_Status = 'DELAYED_30M', Base_Fare = 6400.00 WHERE Flight_ID = 'AI-202'")
    writer_txn.execute("INSERT INTO Reservations (Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES (108, 'AI-202', '22F', 'CONFIRMED')")
    writer_txn.commit()
    timeline.append({
        "Step": "2. Writer-B Updates & Commits",
        "Connection": "Writer-B (Committed)",
        "Flight_Status": "DELAYED_30M",
        "Base_Fare": 6400.0,
        "Res_Count": snap_1["Total_Res"] + 1,
        "MVCC Observation": "Writer did NOT block on Reader-A! New version written.",
    })

    # Step 3: Reader-A queries AGAIN inside its T0 snapshot
    snap_2 = reader_snapshot.fetchall(
        "SELECT f.Flight_ID, f.Flight_Status, f.Base_Fare, COUNT(r.Reservation_ID) AS Total_Res "
        "FROM Flights f LEFT JOIN Reservations r ON f.Flight_ID = r.Flight_ID "
        "WHERE f.Flight_ID = 'AI-202' GROUP BY f.Flight_ID"
    )[0]
    timeline.append({
        "Step": "3. Reader-A Re-Reads Same Query",
        "Connection": "Reader-A (Still in T0)",
        "Flight_Status": snap_2["Flight_Status"],
        "Base_Fare": snap_2["Base_Fare"],
        "Res_Count": snap_2["Total_Res"],
        "MVCC Observation": "Reads historical Undo/WAL snapshot! Consistent Repeat Read ✓",
    })
    reader_snapshot.commit()

    # Step 4: Reader-C opens a fresh transaction after Writer-B committed
    fresh_read = reader_fresh.fetchall(
        "SELECT f.Flight_ID, f.Flight_Status, f.Base_Fare, COUNT(r.Reservation_ID) AS Total_Res "
        "FROM Flights f LEFT JOIN Reservations r ON f.Flight_ID = r.Flight_ID "
        "WHERE f.Flight_ID = 'AI-202' GROUP BY f.Flight_ID"
    )[0]
    timeline.append({
        "Step": "4. Reader-C Fresh Query (Post-Commit)",
        "Connection": "Reader-C (New Read View)",
        "Flight_Status": fresh_read["Flight_Status"],
        "Base_Fare": fresh_read["Base_Fare"],
        "Res_Count": fresh_read["Total_Res"],
        "MVCC Observation": "New Read View sees latest committed version ✓",
    })

    reader_snapshot.close()
    writer_txn.close()
    reader_fresh.close()

    render_table("MVCC Concurrent Snapshot Isolation Verification", timeline)
    assert snap_1 == snap_2, "MVCC Snapshot violated!"
    assert fresh_read["Base_Fare"] == 6400.0, "Committed update not visible to fresh reader!"
    console.print("[green]✓ Verified: Readers never block Writers, and Snapshot Reads remain consistent via Undo/WAL versions.[/green]\n")


if __name__ == "__main__":
    demonstrate_mvcc()
