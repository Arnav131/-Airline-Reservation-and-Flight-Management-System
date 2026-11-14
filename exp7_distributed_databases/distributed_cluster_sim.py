"""
Experiment 7 Core: 3-Node Airport Distributed Database Cluster Simulator.
Each Airport Hub (DEL, BOM, BLR) operates an isolated physical SQLite database shard/replica.
"""
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_core.config import DATA_DIR

NODES_DIR = DATA_DIR / "nodes"
NODES_DIR.mkdir(parents=True, exist_ok=True)


class AirportNode:
    """Represents an autonomous airport operational database node."""

    def __init__(self, node_id: str, airport_code: str, city: str):
        self.node_id = node_id
        self.airport_code = airport_code
        self.city = city
        self.db_path = NODES_DIR / f"node_{airport_code.lower()}.db"
        self.is_partitioned = False  # Simulates network split
        self.replication_queue: list[dict[str, Any]] = []
        self._init_node_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_node_schema(self) -> None:
        conn = self._connect()
        conn.execute("DROP TABLE IF EXISTS Local_Schedule_Replica;")
        conn.execute("DROP TABLE IF EXISTS Reservation_Shard;")
        conn.execute("""
            CREATE TABLE Local_Schedule_Replica (
                Flight_ID           TEXT PRIMARY KEY,
                Source_Airport      TEXT NOT NULL,
                Destination_Airport TEXT NOT NULL,
                Departure_Time      TEXT NOT NULL,
                Flight_Status       TEXT NOT NULL,
                Version_Clock       INTEGER NOT NULL DEFAULT 1,
                Updated_By_Node     TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE Reservation_Shard (
                Reservation_ID INTEGER PRIMARY KEY,
                Passenger_ID   INTEGER NOT NULL,
                Passenger_Name TEXT NOT NULL,
                Flight_ID      TEXT NOT NULL,
                Source_Region  TEXT NOT NULL,
                Seat_Number    TEXT NOT NULL,
                Booking_Status TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    def execute_write(self, sql: str, params: tuple = ()) -> None:
        conn = self._connect()
        conn.execute(sql, params)
        conn.commit()
        conn.close()

    def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        conn = self._connect()
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return rows


class DistributedAirportCluster:
    """Coordinates 3 distributed operational airport nodes: DEL, BOM, BLR."""

    def __init__(self):
        self.nodes: dict[str, AirportNode] = {
            "DEL": AirportNode("Node-1-DEL", "DEL", "New Delhi"),
            "BOM": AirportNode("Node-2-BOM", "BOM", "Mumbai"),
            "BLR": AirportNode("Node-3-BLR", "BLR", "Bengaluru"),
        }

    def get_all_nodes(self) -> list[AirportNode]:
        return list(self.nodes.values())
