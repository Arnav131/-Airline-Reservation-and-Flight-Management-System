"""
Experiment 7.4: Eventual Consistency & Conflict Resolution Across Airport Nodes.
Demonstrates:
  1. Network Partition / Lag: Node DEL updates Flight AI-202 to DELAYED_45M (Version 2)
  2. Temporary Stale Reads: Nodes BOM and BLR temporarily read stale ON_TIME (Version 1)
  3. Concurrent Conflicting Update: Node BOM updates AI-202 to DIVERTED_HYD (Version 3)
  4. Asynchronous Gossip Sync + Last-Write-Wins (Version Clock) Convergence across all 3 nodes!
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import render_table
from exp7_distributed_databases.distributed_cluster_sim import DistributedAirportCluster

console = Console()


def snapshot_flight_state(cluster: DistributedAirportCluster, flight_id: str, phase: str) -> list[dict]:
    rows = []
    for node in cluster.get_all_nodes():
        r = node.query(
            "SELECT Flight_ID, Flight_Status, Version_Clock, Updated_By_Node FROM Local_Schedule_Replica WHERE Flight_ID = ?",
            (flight_id,),
        )[0]
        rows.append(
            {
                "Phase": phase,
                "Node": node.node_id,
                "Flight_ID": r["Flight_ID"],
                "Local_Status": r["Flight_Status"],
                "Version_Clock": r["Version_Clock"],
                "Origin_Node": r["Updated_By_Node"],
            }
        )
    return rows


def run_gossip_sync(cluster: DistributedAirportCluster, flight_id: str) -> None:
    """Anti-entropy gossip protocol converging all replicas using highest Lamport Version_Clock (LWW)."""
    states = []
    for node in cluster.get_all_nodes():
        rec = node.query(
            "SELECT * FROM Local_Schedule_Replica WHERE Flight_ID = ?",
            (flight_id,),
        )[0]
        states.append(rec)

    # Select winning state with highest Version_Clock (and deterministic node tie-breaker)
    winner = max(states, key=lambda x: (x["Version_Clock"], x["Updated_By_Node"]))
    for node in cluster.get_all_nodes():
        node.execute_write(
            """
            UPDATE Local_Schedule_Replica
            SET Flight_Status = ?, Version_Clock = ?, Updated_By_Node = ?
            WHERE Flight_ID = ?
            """,
            (winner["Flight_Status"], winner["Version_Clock"], winner["Updated_By_Node"], flight_id),
        )


def demonstrate_eventual_consistency(cluster: DistributedAirportCluster):
    console.print(Panel.fit("[bold cyan]7.3 Eventual Consistency & Gossip Conflict Convergence[/bold cyan]"))

    node_del = cluster.nodes["DEL"]
    node_bom = cluster.nodes["BOM"]

    trace_rows = []
    trace_rows.extend(snapshot_flight_state(cluster, "AI-202", "1. Initial Consistent"))

    # Step 2: Update at Node DEL during temporary WAN replication delay
    console.print("[yellow]→ Updating AI-202 status at DEL Hub to 'DELAYED_45M' (v=2) while WAN link lags...[/yellow]")
    node_del.execute_write(
        "UPDATE Local_Schedule_Replica SET Flight_Status = 'DELAYED_45M', Version_Clock = 2, Updated_By_Node = 'Node-1-DEL' WHERE Flight_ID = 'AI-202'"
    )
    trace_rows.extend(snapshot_flight_state(cluster, "AI-202", "2. DEL Updated (Stale BOM/BLR)"))

    # Step 3: Concurrent conflicting update at BOM Hub with newer version clock (v=3)
    console.print("[yellow]→ Concurrent update at BOM Hub to 'BOARDING_GATE_B4' (v=3) before DEL update arrived...[/yellow]")
    node_bom.execute_write(
        "UPDATE Local_Schedule_Replica SET Flight_Status = 'BOARDING_GATE_B4', Version_Clock = 3, Updated_By_Node = 'Node-2-BOM' WHERE Flight_ID = 'AI-202'"
    )
    trace_rows.extend(snapshot_flight_state(cluster, "AI-202", "3. Split-Brain Divergence"))

    # Step 4: Simulate network recovery and anti-entropy gossip propagation
    console.print("[dim]⏳ Network partition healed. Running anti-entropy Gossip Sync (Lamport Version Resolution)...[/dim]")
    time.sleep(0.5)
    run_gossip_sync(cluster, "AI-202")
    trace_rows.extend(snapshot_flight_state(cluster, "AI-202", "4. Converged (Consistent)"))

    render_table("Eventual Consistency State Convergence Across DEL, BOM & BLR", trace_rows)

    final_statuses = {
        n.query("SELECT Flight_Status FROM Local_Schedule_Replica WHERE Flight_ID='AI-202'")[0]["Flight_Status"]
        for n in cluster.get_all_nodes()
    }
    assert len(final_statuses) == 1, f"Nodes failed to converge: {final_statuses}"
    console.print(f"[bold green]✓ All 3 airport nodes converged to unified state: {final_statuses.pop()} (Eventual Consistency Verified!)[/bold green]\n")
