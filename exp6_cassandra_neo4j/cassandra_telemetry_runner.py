"""
Experiment 6.1 Runner: Apache Cassandra Wide-Column Telemetry & Event Store.
Uses Flight_ID as Partition Key and event_timestamp DESC as Clustering Key.
Dual-Mode: Connects to live Cassandra (localhost:9042) or Embedded Token-Ring Partition Engine.
"""
import hashlib
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.config import CASSANDRA_CONFIG, is_port_open
from db_core.relational_adapter import render_table

console = Console()


class EmbeddedCassandraCluster:
    """Simulates Cassandra consistent-hashing partition ring with Flight_ID partition key."""

    def __init__(self, num_vnodes: int = 3):
        self.num_vnodes = num_vnodes
        self.flight_activity_log: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.passenger_travel_events: dict[str, list[dict[str, Any]]] = defaultdict(list)

    @staticmethod
    def _partition_token(flight_id: str) -> int:
        digest = hashlib.md5(flight_id.encode()).hexdigest()[:8]
        return int(digest, 16)

    def get_target_node(self, flight_id: str) -> str:
        token = self._partition_token(flight_id)
        return f"Cassandra-Node-{(token % self.num_vnodes) + 1} (Token: {token})"

    def insert_flight_activity(
        self, flight_id: str, event_ts: datetime, event_type: str, airport_code: str, operator_id: str, metadata: dict
    ) -> None:
        self.flight_activity_log[flight_id].append(
            {
                "flight_id": flight_id,
                "event_timestamp": event_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "event_id": str(uuid.uuid4())[:8],
                "event_type": event_type,
                "airport_code": airport_code,
                "operator_id": operator_id,
                "metadata": str(metadata),
            }
        )
        # Maintain clustering order: event_timestamp DESC
        self.flight_activity_log[flight_id].sort(key=lambda r: r["event_timestamp"], reverse=True)

    def insert_passenger_event(
        self, flight_id: str, event_ts: datetime, passenger_id: int, seat_number: str, event_stage: str, gate: str
    ) -> None:
        self.passenger_travel_events[flight_id].append(
            {
                "flight_id": flight_id,
                "event_timestamp": event_ts.strftime("%Y-%m-%d %H:%M:%S"),
                "passenger_id": passenger_id,
                "seat_number": seat_number,
                "event_stage": event_stage,
                "gate_number": gate,
            }
        )
        self.passenger_travel_events[flight_id].sort(key=lambda r: r["event_timestamp"], reverse=True)

    def select_by_flight_id(self, table: str, flight_id: str, limit: int = 10) -> list[dict[str, Any]]:
        store = self.flight_activity_log if table == "flight_activity_log" else self.passenger_travel_events
        return store.get(flight_id, [])[:limit]


def run_cassandra_demo():
    console.print(Panel.fit("[bold cyan]6.1 Apache Cassandra: Wide-Column Telemetry (Partition Key: Flight_ID)[/bold cyan]"))
    live_mode = False

    if is_port_open(CASSANDRA_CONFIG["hosts"][0], CASSANDRA_CONFIG["port"]):
        try:
            from cassandra.cluster import Cluster

            cluster = Cluster(CASSANDRA_CONFIG["hosts"], port=CASSANDRA_CONFIG["port"])
            session = cluster.connect()
            live_mode = True
            console.print("[cyan]Active Engine:[/cyan] [bold]LIVE_CASSANDRA[/bold]\n")
            cql_text = (Path(__file__).parent / "cassandra_schema.cql").read_text(encoding="utf-8")
            for stmt in cql_text.split(";"):
                s = "\n".join(line for line in stmt.splitlines() if not line.strip().startswith("--")).strip()
                if s:
                    session.execute(s)
            cluster.shutdown()
        except Exception:
            live_mode = False

    if not live_mode:
        console.print("[cyan]Active Engine:[/cyan] [bold]EMBEDDED_CASSANDRA_RING[/bold]\n")

    cass = EmbeddedCassandraCluster(num_vnodes=3)
    base_time = datetime(2026, 11, 12, 6, 30, 0)

    # Ingest Flight Activity Events
    events = [
        ("AI-202", base_time, "SCHEDULED", "DEL", "OPS-01", {"gate": "T3-14"}),
        ("AI-202", base_time + timedelta(minutes=60), "BOARDING_OPEN", "DEL", "GATE-14", {"zone": "Priority"}),
        ("AI-202", base_time + timedelta(minutes=110), "GATE_CLOSED", "DEL", "GATE-14", {"pax_boarded": "172"}),
        ("AI-202", base_time + timedelta(minutes=125), "DEPARTED", "DEL", "ATC-DEL", {"runway": "29L"}),
        ("AI-510", base_time + timedelta(hours=10), "SCHEDULED", "DEL", "OPS-02", {"gate": "T3-02"}),
        ("AI-304", base_time + timedelta(hours=4), "DELAYED_WEATHER", "BOM", "OPS-BOM", {"delay_min": "25"}),
    ]
    for fid, ts, etype, ap, op, meta in events:
        cass.insert_flight_activity(fid, ts, etype, ap, op, meta)

    # Ingest Passenger Travel Events
    pax_events = [
        ("AI-202", base_time + timedelta(minutes=30), 101, "12A", "CHECKIN", "T3-Kiosk"),
        ("AI-202", base_time + timedelta(minutes=45), 101, "12A", "BAG_DROP", "Belt-04"),
        ("AI-202", base_time + timedelta(minutes=65), 102, "12B", "SECURITY_PASS", "Lane-02"),
        ("AI-202", base_time + timedelta(minutes=95), 101, "12A", "BOARDED", "T3-14"),
    ]
    for fid, ts, pid, seat, stage, gate in pax_events:
        cass.insert_passenger_event(fid, ts, pid, seat, stage, gate)

    # Show Partition Token Distribution
    token_rows = [
        {"Flight_ID (Partition Key)": fid, "Assigned Ring Node & Token": cass.get_target_node(fid)}
        for fid in ["AI-202", "AI-304", "AI-510"]
    ]
    render_table("Cassandra Partition Key Placement (Consistent Hashing)", token_rows)

    # Query single partition (DESC clustering order)
    ai202_logs = cass.select_by_flight_id("flight_activity_log", "AI-202")
    render_table("Query: SELECT * FROM flight_activity_log WHERE flight_id = 'AI-202' (DESC Order)", ai202_logs)

    ai202_pax = cass.select_by_flight_id("passenger_travel_events", "AI-202")
    render_table("Query: SELECT * FROM passenger_travel_events WHERE flight_id = 'AI-202'", ai202_pax)


if __name__ == "__main__":
    run_cassandra_demo()
