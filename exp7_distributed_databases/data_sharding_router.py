"""
Experiment 7.1 & 7.3: Partitioning & Sharding of Passenger Reservations.
Demonstrates:
  - Regional Partitioning by Source Airport (DEL, BOM, BLR)
  - Consistent Hash Sharding by Flight_ID across the 3 nodes
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import render_table
from exp7_distributed_databases.distributed_cluster_sim import DistributedAirportCluster

console = Console()


class ShardingRouter:
    """Routes passenger reservation records across distributed airport shard nodes."""

    def __init__(self, cluster: DistributedAirportCluster):
        self.cluster = cluster
        self.node_keys = list(cluster.nodes.keys())  # ['DEL', 'BOM', 'BLR']

    def route_by_region(self, source_airport: str) -> str:
        """Range/List Partitioning by airport region."""
        return source_airport if source_airport in self.cluster.nodes else "DEL"

    def route_by_flight_hash(self, flight_id: str) -> str:
        """Consistent Hash Sharding by Flight_ID."""
        digest = int(hashlib.sha256(flight_id.encode()).hexdigest()[:8], 16)
        return self.node_keys[digest % len(self.node_keys)]

    def insert_reservation_sharded(self, record: dict, strategy: str = "region") -> str:
        target_code = (
            self.route_by_region(record["Source_Region"])
            if strategy == "region"
            else self.route_by_flight_hash(record["Flight_ID"])
        )
        node = self.cluster.nodes[target_code]
        node.execute_write(
            """
            INSERT OR REPLACE INTO Reservation_Shard
                (Reservation_ID, Passenger_ID, Passenger_Name, Flight_ID, Source_Region, Seat_Number, Booking_Status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["Reservation_ID"],
                record["Passenger_ID"],
                record["Passenger_Name"],
                record["Flight_ID"],
                record["Source_Region"],
                record["Seat_Number"],
                record["Booking_Status"],
            ),
        )
        return node.node_id


def run_sharding_demo(cluster: DistributedAirportCluster):
    console.print(Panel.fit("[bold cyan]7.1 Airport Partitioning & Horizontal Sharding of Reservations[/bold cyan]"))
    router = ShardingRouter(cluster)

    sample_reservations = [
        {"Reservation_ID": 1001, "Passenger_ID": 101, "Passenger_Name": "Aarav Sharma", "Flight_ID": "AI-202", "Source_Region": "DEL", "Seat_Number": "12A", "Booking_Status": "CONFIRMED"},
        {"Reservation_ID": 1002, "Passenger_ID": 102, "Passenger_Name": "Diya Patel", "Flight_ID": "AI-202", "Source_Region": "DEL", "Seat_Number": "12B", "Booking_Status": "CONFIRMED"},
        {"Reservation_ID": 1003, "Passenger_ID": 103, "Passenger_Name": "Rohan Verma", "Flight_ID": "AI-304", "Source_Region": "BOM", "Seat_Number": "04C", "Booking_Status": "CONFIRMED"},
        {"Reservation_ID": 1004, "Passenger_ID": 104, "Passenger_Name": "Ananya Iyer", "Flight_ID": "AI-510", "Source_Region": "DEL", "Seat_Number": "01A", "Booking_Status": "CONFIRMED"},
        {"Reservation_ID": 1005, "Passenger_ID": 105, "Passenger_Name": "Kabir Malhotra", "Flight_ID": "AI-612", "Source_Region": "BOM", "Seat_Number": "02F", "Booking_Status": "CONFIRMED"},
        {"Reservation_ID": 1007, "Passenger_ID": 107, "Passenger_Name": "Vikramaditya Rao", "Flight_ID": "AI-715", "Source_Region": "DEL", "Seat_Number": "18A", "Booking_Status": "CONFIRMED"},
        {"Reservation_ID": 1008, "Passenger_ID": 108, "Passenger_Name": "Sneha Kulkarni", "Flight_ID": "AI-820", "Source_Region": "BLR", "Seat_Number": "06K", "Booking_Status": "CONFIRMED"},
        {"Reservation_ID": 1009, "Passenger_ID": 106, "Passenger_Name": "Meera Nair", "Flight_ID": "AI-408", "Source_Region": "BLR", "Seat_Number": "09D", "Booking_Status": "CONFIRMED"},
    ]

    routing_log = []
    for rec in sample_reservations:
        target_node = router.insert_reservation_sharded(rec, strategy="region")
        hash_shard = cluster.nodes[router.route_by_flight_hash(rec["Flight_ID"])].node_id
        routing_log.append(
            {
                "Reservation_ID": rec["Reservation_ID"],
                "Passenger": rec["Passenger_Name"],
                "Flight_ID": rec["Flight_ID"],
                "Region_Partition": target_node,
                "Flight_Hash_Shard": hash_shard,
            }
        )

    render_table("Horizontal Sharding Routing Matrix (Region Partitioning + Hash Sharding)", routing_log)

    shard_stats = []
    for code, node in cluster.nodes.items():
        rows = node.query("SELECT * FROM Reservation_Shard")
        shard_stats.append(
            {
                "Airport_Node": node.node_id,
                "Physical_DB_File": node.db_path.name,
                "Stored_Reservations": len(rows),
                "Flight_IDs_Hosted": ", ".join(sorted({r["Flight_ID"] for r in rows})),
            }
        )
    render_table("Physical Storage Distribution Across 3 Airport Nodes", shard_stats)
