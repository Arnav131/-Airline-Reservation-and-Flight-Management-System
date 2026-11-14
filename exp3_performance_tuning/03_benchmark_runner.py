"""
Experiment 3 Runner: Performance Optimization & Indexing Benchmark.
Demonstrates:
  - Query plan inspection via EXPLAIN / EXPLAIN QUERY PLAN
  - B-Tree Indexes on Flight_ID, Passenger_ID, and Composite Search Routes
  - Computed Hash Column (SHA-256) for Ticket Reference Lookup
  - Before-vs-After Latency Comparison across 25,000 Reservations
"""
import hashlib
import random
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.config import DATA_DIR
from db_core.relational_adapter import render_table

console = Console()
BENCH_DB_PATH = DATA_DIR / "iarfms_benchmark.db"


def setup_benchmark_dataset(num_flights: int = 2000, num_reservations: int = 25000) -> sqlite3.Connection:
    """Build a fresh 25k-row unindexed relational database for clean before/after benchmarking."""
    if BENCH_DB_PATH.exists():
        BENCH_DB_PATH.unlink()

    conn = sqlite3.connect(str(BENCH_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")

    conn.execute("""
        CREATE TABLE Flights_Bench (
            Flight_ID           TEXT PRIMARY KEY,
            Source_Airport      TEXT NOT NULL,
            Destination_Airport TEXT NOT NULL,
            Departure_Time      TEXT NOT NULL,
            Base_Fare           REAL NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE Reservations_Bench (
            Reservation_ID INTEGER PRIMARY KEY,
            Passenger_ID   INTEGER NOT NULL,
            Flight_ID      TEXT NOT NULL,
            Seat_Number    TEXT NOT NULL,
            Booking_Status TEXT NOT NULL,
            Ticket_Ref_Str TEXT NOT NULL
        );
    """)

    airports = ["DEL", "BOM", "BLR", "MAA", "HYD", "DXB", "SIN", "LHR"]
    flights = []
    for i in range(1, num_flights + 1):
        src, dst = random.sample(airports, 2)
        day = (i % 28) + 1
        hr = i % 24
        flights.append((f"FL-{i:04d}", src, dst, f"2026-11-{day:02d} {hr:02d}:00:00", random.uniform(3000, 35000)))

    conn.executemany("INSERT INTO Flights_Bench VALUES (?, ?, ?, ?, ?)", flights)

    reservations = []
    statuses = ["CONFIRMED", "CONFIRMED", "CONFIRMED", "PENDING", "CANCELLED"]
    for r_id in range(1, num_reservations + 1):
        p_id = random.randint(1, 5000)
        f_id = f"FL-{random.randint(1, num_flights):04d}"
        seat = f"{random.randint(1, 45):02d}{random.choice('ABCDEF')}"
        status = random.choice(statuses)
        ref_str = f"{r_id}-{p_id}-{f_id}-{seat}"
        reservations.append((r_id, p_id, f_id, seat, status, ref_str))

    conn.executemany("INSERT INTO Reservations_Bench VALUES (?, ?, ?, ?, ?, ?)", reservations)
    conn.commit()
    return conn


def explain_plan(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> str:
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return " | ".join(r["detail"] for r in rows)


def time_query(conn: sqlite3.Connection, sql: str, param_list: list[tuple]) -> tuple[float, float]:
    """Execute queries for each param tuple and return (avg_ms, total_ms)."""
    t0 = time.perf_counter()
    for p in param_list:
        conn.execute(sql, p).fetchall()
    t1 = time.perf_counter()
    total_ms = (t1 - t0) * 1000.0
    avg_ms = total_ms / len(param_list)
    return round(avg_ms, 4), round(total_ms, 2)


def run_experiment_3():
    console.print(Panel.fit("[bold green]EXPERIMENT 3: Performance Optimization (EXPLAIN, B-Tree & Computed Hash)[/bold green]"))
    console.print("[cyan]Generating 2,000 Flights & 25,000 Reservation synthetic records for benchmark...[/cyan]")
    conn = setup_benchmark_dataset(2000, 25000)
    console.print("[green]✓ Synthetic dataset ready (27,000 total rows).[/green]\n")

    # Sample parameters for 150 repetitions per query type
    sample_flights = [(f"FL-{random.randint(1, 2000):04d}",) for _ in range(150)]
    sample_passengers = [(random.randint(1, 5000),) for _ in range(150)]
    sample_routes = [("DEL", "BOM", "2026-11-10 00:00:00") for _ in range(150)]

    # Pick known ticket refs for lookup benchmark
    sample_rows = conn.execute("SELECT Reservation_ID, Passenger_ID, Flight_ID, Seat_Number, Ticket_Ref_Str FROM Reservations_Bench ORDER BY RANDOM() LIMIT 150").fetchall()
    sample_refs_unindexed = [(r["Ticket_Ref_Str"],) for r in sample_rows]
    sample_hashes = [(hashlib.sha256(r["Ticket_Ref_Str"].encode()).hexdigest(),) for r in sample_rows]

    q_flight = "SELECT Reservation_ID, Passenger_ID, Seat_Number FROM Reservations_Bench WHERE Flight_ID = ? AND Booking_Status = 'CONFIRMED'"
    q_passenger = "SELECT Reservation_ID, Flight_ID, Seat_Number FROM Reservations_Bench WHERE Passenger_ID = ?"
    q_route = "SELECT Flight_ID, Departure_Time, Base_Fare FROM Flights_Bench WHERE Source_Airport = ? AND Destination_Airport = ? AND Departure_Time >= ?"
    q_hash_before = "SELECT Reservation_ID, Flight_ID, Seat_Number FROM Reservations_Bench WHERE Ticket_Ref_Str = ?"

    # 1. BEFORE INDEXING
    plan_f_before = explain_plan(conn, q_flight, sample_flights[0])
    plan_p_before = explain_plan(conn, q_passenger, sample_passengers[0])
    plan_r_before = explain_plan(conn, q_route, sample_routes[0])
    plan_h_before = explain_plan(conn, q_hash_before, sample_refs_unindexed[0])

    avg_f_b, tot_f_b = time_query(conn, q_flight, sample_flights)
    avg_p_b, tot_p_b = time_query(conn, q_passenger, sample_passengers)
    avg_r_b, tot_r_b = time_query(conn, q_route, sample_routes)
    avg_h_b, tot_h_b = time_query(conn, q_hash_before, sample_refs_unindexed)

    # 2. APPLY B-TREE INDEXES + COMPUTED HASH COLUMN
    console.print("[bold yellow]Applying B-Tree Indexes & Computed SHA-256 Hash Column...[/bold yellow]")
    conn.execute("CREATE INDEX idx_bench_res_flight ON Reservations_Bench(Flight_ID, Booking_Status);")
    conn.execute("CREATE INDEX idx_bench_res_passenger ON Reservations_Bench(Passenger_ID);")
    conn.execute("CREATE INDEX idx_bench_flights_route ON Flights_Bench(Source_Airport, Destination_Airport, Departure_Time);")

    # Computed hash column (stored + indexed)
    conn.execute("ALTER TABLE Reservations_Bench ADD COLUMN Ticket_Ref_Hash TEXT;")
    # Populate computed SHA-256 hash deterministically (simulating GENERATED ALWAYS AS SHA2(...) STORED)
    all_rows = conn.execute("SELECT Reservation_ID, Ticket_Ref_Str FROM Reservations_Bench").fetchall()
    hash_updates = [
        (hashlib.sha256(r["Ticket_Ref_Str"].encode()).hexdigest(), r["Reservation_ID"])
        for r in all_rows
    ]
    conn.executemany("UPDATE Reservations_Bench SET Ticket_Ref_Hash = ? WHERE Reservation_ID = ?", hash_updates)
    conn.execute("CREATE UNIQUE INDEX idx_bench_ticket_hash ON Reservations_Bench(Ticket_Ref_Hash);")
    conn.commit()
    console.print("[green]✓ Indexes & Computed Ticket_Ref_Hash column created and populated.[/green]\n")

    q_hash_after = "SELECT Reservation_ID, Flight_ID, Seat_Number FROM Reservations_Bench WHERE Ticket_Ref_Hash = ?"

    # 3. AFTER INDEXING
    plan_f_after = explain_plan(conn, q_flight, sample_flights[0])
    plan_p_after = explain_plan(conn, q_passenger, sample_passengers[0])
    plan_r_after = explain_plan(conn, q_route, sample_routes[0])
    plan_h_after = explain_plan(conn, q_hash_after, sample_hashes[0])

    avg_f_a, tot_f_a = time_query(conn, q_flight, sample_flights)
    avg_p_a, tot_p_a = time_query(conn, q_passenger, sample_passengers)
    avg_r_a, tot_r_a = time_query(conn, q_route, sample_routes)
    avg_h_a, tot_h_a = time_query(conn, q_hash_after, sample_hashes)

    # 4. EXPLAIN Comparison Table
    explain_rows = [
        {"Query Target": "Reservation by Flight_ID", "Before Indexing (EXPLAIN)": plan_f_before, "After Indexing (EXPLAIN)": plan_f_after},
        {"Query Target": "Reservation by Passenger_ID", "Before Indexing (EXPLAIN)": plan_p_before, "After Indexing (EXPLAIN)": plan_p_after},
        {"Query Target": "Flight Search (Route + Date)", "Before Indexing (EXPLAIN)": plan_r_before, "After Indexing (EXPLAIN)": plan_r_after},
        {"Query Target": "Ticket Ref Hash Lookup", "Before Indexing (EXPLAIN)": plan_h_before, "After Indexing (EXPLAIN)": plan_h_after},
    ]
    render_table("EXPLAIN Query Execution Plan Comparison", explain_rows)

    # 5. Latency & Speedup Comparison Table
    def speedup(b, a):
        return f"{round(b / max(a, 0.0001), 1)}x faster"

    perf_rows = [
        {
            "Workload (150 Queries)": "Filter Reservations by Flight_ID",
            "Before Avg (ms)": avg_f_b,
            "After Avg (ms)": avg_f_a,
            "Before Total (ms)": tot_f_b,
            "After Total (ms)": tot_f_a,
            "Speedup": speedup(tot_f_b, tot_f_a),
        },
        {
            "Workload (150 Queries)": "Filter Reservations by Passenger_ID",
            "Before Avg (ms)": avg_p_b,
            "After Avg (ms)": avg_p_a,
            "Before Total (ms)": tot_p_b,
            "After Total (ms)": tot_p_a,
            "Speedup": speedup(tot_p_b, tot_p_a),
        },
        {
            "Workload (150 Queries)": "Composite Route Search (Src+Dst+Time)",
            "Before Avg (ms)": avg_r_b,
            "After Avg (ms)": avg_r_a,
            "Before Total (ms)": tot_r_b,
            "After Total (ms)": tot_r_a,
            "Speedup": speedup(tot_r_b, tot_r_a),
        },
        {
            "Workload (150 Queries)": "Computed SHA-256 Ticket Hash Lookup",
            "Before Avg (ms)": avg_h_b,
            "After Avg (ms)": avg_h_a,
            "Before Total (ms)": tot_h_b,
            "After Total (ms)": tot_h_a,
            "Speedup": speedup(tot_h_b, tot_h_a),
        },
    ]
    render_table("Benchmark Results: Before vs After Indexing (25,000 Rows)", perf_rows)
    conn.close()


if __name__ == "__main__":
    run_experiment_3()
