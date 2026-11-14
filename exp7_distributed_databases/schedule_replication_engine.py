"""
Experiment 7.2: Master-Replica Flight Schedule Replication Across All Airport Nodes.
Ensures every airport hub (DEL, BOM, BLR) holds an identical local replica of flight schedules
for ultra-fast, partition-tolerant local schedule lookups.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import render_table
from exp7_distributed_databases.distributed_cluster_sim import DistributedAirportCluster

console = Console()


def replicate_schedules_across_cluster(cluster: DistributedAirportCluster) -> None:
    console.print(Panel.fit("[bold cyan]7.2 Global Flight Schedule Replication Across 3 Airport Nodes (RF=3)[/bold cyan]"))

    master_schedules = [
        ("AI-202", "DEL", "BOM", "2026-11-12 08:30:00", "ON_TIME", 1, "HQ-MASTER"),
        ("AI-304", "BOM", "BLR", "2026-11-12 11:45:00", "ON_TIME", 1, "HQ-MASTER"),
        ("AI-408", "BLR", "MAA", "2026-11-12 15:15:00", "ON_TIME", 1, "HQ-MASTER"),
        ("AI-510", "DEL", "DXB", "2026-11-12 20:00:00", "ON_TIME", 1, "HQ-MASTER"),
    ]

    for node in cluster.get_all_nodes():
        for sched in master_schedules:
            node.execute_write(
                """
                INSERT OR REPLACE INTO Local_Schedule_Replica
                    (Flight_ID, Source_Airport, Destination_Airport, Departure_Time, Flight_Status, Version_Clock, Updated_By_Node)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                sched,
            )

    summary = []
    for node in cluster.get_all_nodes():
        rows = node.query("SELECT Flight_ID, Flight_Status, Version_Clock FROM Local_Schedule_Replica ORDER BY Flight_ID")
        summary.append(
            {
                "Node": node.node_id,
                "City": node.city,
                "Replicated_Flights": len(rows),
                "AI-202 Status": next(r["Flight_Status"] for r in rows if r["Flight_ID"] == "AI-202"),
                "Version_Clock": next(r["Version_Clock"] for r in rows if r["Flight_ID"] == "AI-202"),
            }
        )
    render_table("Schedule Replication Verification (All 3 Nodes Hold Identical RF=3 Replicas)", summary)
