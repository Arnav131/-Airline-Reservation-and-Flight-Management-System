"""
Interactive CLI Dashboard & Viva Evaluation Runner for IARFMS (Group 4).
Usage:
  python app/cli_dashboard.py           # Interactive Menu
  python app/cli_dashboard.py --all     # Non-interactive Sequential Run of Experiments 1-7
"""
import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from db_core.config import get_system_status

console = Console()


def render_banner() -> None:
    banner_text = Text()
    banner_text.append("✈️  IARFMS: INTEGRATED AIRLINE RESERVATION & FLIGHT MANAGEMENT SYSTEM\n", style="bold cyan")
    banner_text.append("   Group 4 | Advanced Multi-Model Database System (Experiments 1 – 7)\n", style="bold white")
    banner_text.append("   Relational • Advanced MySQL • Benchmarks • Concurrency • Redis • MongoDB • Cassandra • Neo4j • Distributed", style="dim")
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def show_system_health() -> None:
    status = get_system_status()
    tbl = Table(title="🔌 Database Engine Runtime Detection", show_header=True, header_style="bold magenta", expand=False)
    tbl.add_column("Paradigm", style="cyan")
    tbl.add_column("Target Service", style="white")
    tbl.add_column("Active Mode", style="bold")

    engines = [
        ("Relational OLTP Core", "MySQL 8.0 (:3306)", status["mysql"], "SQLite WAL + Trigger/Txn Dual-Engine"),
        ("In-Memory Key-Value", "Redis 7 (:6379)", status["redis"], "Embedded TTL Lock & Cache Engine"),
        ("Document Store", "MongoDB 6 (:27017)", status["mongodb"], "Embedded Document & Aggregation Engine"),
        ("Wide-Column Big Data", "Cassandra 4 (:9042)", status["cassandra"], "Embedded Token-Ring Partitioner"),
        ("Property Graph Store", "Neo4j 5 (:7687)", status["neo4j"], "Embedded NetworkX MultiDiGraph Pathfinder"),
    ]
    for paradigm, svc, live, fallback in engines:
        mode_str = "[green]LIVE CONTAINER[/green]" if live else f"[yellow]DUAL-MODE ({fallback})[/yellow]"
        tbl.add_row(paradigm, svc, mode_str)
    console.print(tbl)
    console.print("[dim]Tip: Start Docker Desktop and run 'docker-compose up -d' for live containers, or use seamless Dual-Mode.[/dim]\n")


def run_experiment(num: int) -> None:
    modules = {
        1: ("exp1_relational_sql.exp1_runner", "run_experiment_1"),
        2: ("exp2_advanced_mysql.exp2_runner", "run_experiment_2"),
        3: ("exp3_performance_tuning.03_benchmark_runner", "run_experiment_3"),
        4: ("exp4_transaction_concurrency.exp4_runner", "run_experiment_4"),
        5: ("exp5_redis_mongodb.exp5_runner", "run_experiment_5"),
        6: ("exp6_cassandra_neo4j.exp6_runner", "run_experiment_6"),
        7: ("exp7_distributed_databases.exp7_runner", "run_experiment_7"),
    }
    if num in modules:
        mod_name, func_name = modules[num]
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
        func()


def run_all_experiments() -> None:
    render_banner()
    show_system_health()
    console.print("[bold green]🚀 Running all 7 experiments sequentially...[/bold green]\n")
    for i in range(1, 8):
        run_experiment(i)
    console.print("[bold green]✅ All 7 experiments completed successfully![/bold green]\n")


def show_viva_cheat_sheet() -> None:
    console.print(Panel.fit("[bold cyan]🎓 Faculty Evaluation & Viva Voce Quick Reference[/bold cyan]"))
    qas = [
        ("Q: Why use a TRIGGER for duplicate seat checks instead of a UNIQUE constraint?",
         "A UNIQUE constraint on (Flight_ID, Seat_Number) would prevent re-booking if a ticket was CANCELLED. Our trigger checks active status (CONFIRMED/PENDING) only."),
        ("Q: What is the difference between LOCK IN SHARE MODE and FOR UPDATE?",
         "SHARE (S-lock) allows concurrent readers but blocks writers. FOR UPDATE (X-lock) blocks both concurrent readers and writers, preventing double bookings."),
        ("Q: How does MVCC work in InnoDB?",
         "Readers don't block writers and writers don't block readers. InnoDB keeps historical row snapshots in Undo logs using transaction Read Views."),
        ("Q: Why is Cassandra used for flight telemetry over relational tables?",
         "Cassandra uses LSM-trees for microsecond sequential writes and partitions by Flight_ID, keeping telemetry sequentially clustered by timestamp."),
        ("Q: How does Neo4j solve connecting flights better than SQL?",
         "SQL requires recursive multi-table self-joins (O(N^k)). Neo4j uses Index-Free Adjacency (direct pointer traversals) evaluating routes in milliseconds."),
        ("Q: Explain CAP theorem in your 3-airport cluster.",
         "During network partition (P), seat bookings prioritize Consistency (CP), while flight schedule viewing prioritizes Availability with Eventual Consistency (AP)."),
    ]
    for q, a in qas:
        console.print(f"[bold yellow]{q}[/bold yellow]")
        console.print(f"[white]{a}[/white]\n")


def interactive_menu() -> None:
    while True:
        try:
            render_banner()
            show_system_health()

            menu = Table(title="📋 Experiment Navigation Menu", show_header=True, header_style="bold blue")
            menu.add_column("Key", style="bold cyan", justify="center")
            menu.add_column("Experiment Task Description", style="white")

            items = [
                ("1", "Experiment 1: Relational SQL (7 Tables, Multi-Table JOINs, RBAC, TCL Savepoints)"),
                ("2", "Experiment 2: Advanced MySQL (Views, Duplicate-Seat Trigger, Procedure, Function, Cursor)"),
                ("3", "Experiment 3: Performance Optimization (EXPLAIN Plans, B-Tree, SHA-256 Hash, 25k Benchmark)"),
                ("4", "Experiment 4: Transaction Concurrency (ACID Proof, 8-Thread Seat Race, S/X Locks, Deadlock, MVCC)"),
                ("5", "Experiment 5: Redis & MongoDB (Sessions, Route Cache, 10m Seat-Hold TTL, Mongo Aggregations)"),
                ("6", "Experiment 6: Cassandra & Neo4j (Flight_ID Telemetry Partitioning & Connecting Flight Pathfinder)"),
                ("7", "Experiment 7: Distributed Cluster (3 Airport Nodes, Sharding, Replication, Eventual Consistency)"),
                ("A", "Run ALL 7 Experiments Sequentially (Full Demo)"),
                ("T", "Run Complete Automated Pytest Verification Suite"),
                ("V", "View Faculty Viva Voce Quick Cheat Sheet"),
                ("0", "Exit Dashboard"),
            ]
            for k, desc in items:
                menu.add_row(f"[{k}]", desc)
            console.print(menu)

            choice = console.input("\n[bold green]Select an option [0-7, A, T, V]: [/bold green]").strip().upper()

            if choice == "0":
                console.print("\n[cyan]👋 Exiting IARFMS Dashboard. Best of luck with your evaluation![/cyan]")
                break
            elif choice in {"1", "2", "3", "4", "5", "6", "7"}:
                console.clear()
                run_experiment(int(choice))
                console.input("\n[dim]Press Enter to return to menu...[/dim]")
                console.clear()
            elif choice == "A":
                console.clear()
                run_all_experiments()
                console.input("\n[dim]Press Enter to return to menu...[/dim]")
                console.clear()
            elif choice == "T":
                console.clear()
                console.print("[bold cyan]🧪 Running Pytest Suite...[/bold cyan]\n")
                subprocess.run([sys.executable, "-m", "pytest", str(BASE_DIR / "tests" / "test_all_experiments.py"), "-v"], check=False)
                console.input("\n[dim]Press Enter to return to menu...[/dim]")
                console.clear()
            elif choice == "V":
                console.clear()
                show_viva_cheat_sheet()
                console.input("\n[dim]Press Enter to return to menu...[/dim]")
                console.clear()
            else:
                console.print("[red]Invalid choice. Please select 0-7, A, T, or V.[/red]\n")
        except KeyboardInterrupt:
            console.print("\n\n[cyan]👋 Exiting IARFMS Dashboard.[/cyan]")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IARFMS Interactive Evaluation Dashboard")
    parser.add_argument("--all", action="store_true", help="Run all 7 experiments sequentially and exit.")
    args = parser.parse_args()
    if args.all:
        run_all_experiments()
    else:
        interactive_menu()
