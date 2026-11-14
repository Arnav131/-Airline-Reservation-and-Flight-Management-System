"""
Experiment 4.2: Multi-Threaded Concurrent Seat Booking Race Condition Simulation.
8 Passengers simultaneously attempt to reserve Seat 16A on Flight AI-202 at the exact same instant.
Demonstrates how DB locks + Triggers guarantee zero double-bookings.
"""
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import RelationalConnection, render_table
from exp1_relational_sql.exp1_runner import init_schema_and_seed
from exp2_advanced_mysql.exp2_runner import setup_views_and_triggers

console = Console()


def simulate_concurrent_seat_race(num_passengers: int = 8, target_flight: str = "AI-202", target_seat: str = "16A"):
    console.print(Panel.fit("[bold cyan]4.2 Concurrent Seat Booking Race Condition Simulation[/bold cyan]"))
    db = RelationalConnection()
    init_schema_and_seed(db)
    setup_views_and_triggers(db)
    db.close()

    barrier = threading.Barrier(num_passengers)
    results = []
    results_lock = threading.Lock()

    def attempt_booking(passenger_idx: int):
        passenger_id = 101 + (passenger_idx % 8)
        conn = RelationalConnection()
        # Wait so all threads hit the database at the exact same microsecond
        barrier.wait()
        try:
            conn.execute("BEGIN IMMEDIATE" if conn.mode == "sqlite" else "START TRANSACTION")
            if conn.mode == "mysql":
                existing = conn.fetchall(
                    "SELECT Reservation_ID FROM Reservations WHERE Flight_ID = %s AND Seat_Number = %s AND Booking_Status = 'CONFIRMED' FOR UPDATE",
                    (target_flight, target_seat),
                )
            else:
                existing = conn.fetchall(
                    "SELECT Reservation_ID FROM Reservations WHERE Flight_ID = ? AND Seat_Number = ? AND Booking_Status = 'CONFIRMED'",
                    (target_flight, target_seat),
                )

            if existing:
                conn.rollback()
                outcome = "REJECTED (Seat Already Booked)"
                success = False
            else:
                cur = conn.execute(
                    "INSERT INTO Reservations (Passenger_ID, Flight_ID, Seat_Number, Booking_Status) VALUES (?, ?, ?, 'CONFIRMED')",
                    (passenger_id, target_flight, target_seat),
                )
                conn.execute(
                    "INSERT INTO Payments (Reservation_ID, Amount, Payment_Status) VALUES (?, 5200.00, 'SUCCESS')",
                    (cur.lastrowid,),
                )
                conn.commit()
                outcome = f"WON SEAT! (Reservation #{cur.lastrowid})"
                success = True
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            outcome = f"BLOCKED ({str(exc).splitlines()[0][:55]})"
            success = False
        finally:
            conn.close()

        with results_lock:
            results.append(
                {
                    "Thread": f"Passenger-Thread-{passenger_idx + 1}",
                    "Passenger_ID": passenger_id,
                    "Target": f"{target_flight} / {target_seat}",
                    "Success": "YES" if success else "NO",
                    "Outcome": outcome,
                }
            )

    with ThreadPoolExecutor(max_workers=num_passengers) as pool:
        for i in range(num_passengers):
            pool.submit(attempt_booking, i)

    results.sort(key=lambda r: r["Thread"])
    render_table(f"Race Condition Results ({num_passengers} Concurrent Requests for {target_flight} Seat {target_seat})", results)

    winners = [r for r in results if r["Success"] == "YES"]
    console.print(f"[bold green]✓ Exactly {len(winners)} winner(s) recorded. Zero double-bookings occurred![/bold green]\n")
    assert len(winners) == 1, f"Expected 1 winner, got {len(winners)}"


if __name__ == "__main__":
    simulate_concurrent_seat_race()
