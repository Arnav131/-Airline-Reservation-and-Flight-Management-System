"""Helper to print the CLI menu for screenshot capture."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.cli_dashboard import render_banner, show_system_health, console
from rich.table import Table

render_banner()
show_system_health()

menu = Table(title="📋 Experiment Navigation Menu", show_header=True, header_style="bold blue")
menu.add_column("Key", style="bold cyan", justify="center")
menu.add_column("Experiment Task Description", style="white")

menu.add_row("[1]", "Experiment 1: Relational SQL (7 Tables, Multi-Table JOINs, RBAC, TCL Savepoints)")
menu.add_row("[2]", "Experiment 2: Advanced MySQL (Views, Duplicate-Seat Trigger, Procedure, Function, Cursor)")
menu.add_row("[3]", "Experiment 3: Performance Optimization (EXPLAIN Plans, B-Tree, SHA-256 Hash, 25k Benchmark)")
menu.add_row("[4]", "Experiment 4: Transaction Concurrency (ACID Proof, 8-Thread Seat Race, S/X Locks, Deadlock, MVCC)")
menu.add_row("[5]", "Experiment 5: Redis & MongoDB (Sessions, Route Cache, 10m Seat-Hold TTL, Mongo Aggregations)")
menu.add_row("[6]", "Experiment 6: Cassandra & Neo4j (Flight_ID Telemetry Partitioning & Connecting Flight Pathfinder)")
menu.add_row("[7]", "Experiment 7: Distributed Cluster (3 Airport Nodes, Sharding, Replication, Eventual Consistency)")
menu.add_row("[A]", "Run ALL 7 Experiments Sequentially (Full Demo)")
menu.add_row("[T]", "Run Complete Automated Pytest Verification Suite")
menu.add_row("[V]", "View Faculty Viva Voce Quick Cheat Sheet")
menu.add_row("[0]", "Exit Dashboard")

console.print(menu)
console.print("\n[bold green]Ready for faculty evaluation input...[/bold green]")
