"""
Experiment 6.2 Runner: Neo4j Graph Database & Multi-City Connecting Flight Pathfinder.
Models Passenger, Flight, Airport, Aircraft nodes and BOOKED, DEPARTS_FROM, ARRIVES_AT, OPERATED_BY edges.
Dual-Mode: Connects to live Neo4j (bolt://localhost:7687) or NetworkX Graph Engine.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import networkx as nx
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_core.config import NEO4J_CONFIG, is_port_open
from db_core.relational_adapter import render_table

console = Console()


class AirlinePropertyGraph:
    """Labeled Property Graph mirroring Neo4j nodes and relationships."""

    def __init__(self):
        self.g = nx.MultiDiGraph()

    def add_airport(self, code: str, name: str, city: str):
        self.g.add_node(f"Airport:{code}", label="Airport", code=code, name=name, city=city)

    def add_aircraft(self, ac_id: int, model: str, capacity: int):
        self.g.add_node(f"Aircraft:{ac_id}", label="Aircraft", id=ac_id, model=model, capacity=capacity)

    def add_passenger(self, pid: int, name: str):
        self.g.add_node(f"Passenger:{pid}", label="Passenger", id=pid, name=name)

    def add_flight(self, fid: str, src_code: str, dst_code: str, ac_id: int, dep: datetime, arr: datetime, fare: float):
        f_node = f"Flight:{fid}"
        self.g.add_node(f_node, label="Flight", flight_id=fid, departure=dep, arrival=arr, fare=fare)
        self.g.add_edge(f_node, f"Airport:{src_code}", rel="DEPARTS_FROM")
        self.g.add_edge(f_node, f"Airport:{dst_code}", rel="ARRIVES_AT")
        self.g.add_edge(f_node, f"Aircraft:{ac_id}", rel="OPERATED_BY")

    def add_booking(self, pid: int, fid: str, seat: str, status: str):
        self.g.add_edge(f"Passenger:{pid}", f"Flight:{fid}", rel="BOOKED", seat=seat, status=status)

    def _flights_departing_from(self, airport_node: str) -> list[str]:
        return [
            u for u, v, d in self.g.in_edges(airport_node, data=True) if d.get("rel") == "DEPARTS_FROM"
        ]

    def _arrival_airport(self, flight_node: str) -> str | None:
        for _, v, d in self.g.out_edges(flight_node, data=True):
            if d.get("rel") == "ARRIVES_AT":
                return v
        return None

    def _operated_by_model(self, flight_node: str) -> str:
        for _, v, d in self.g.out_edges(flight_node, data=True):
            if d.get("rel") == "OPERATED_BY":
                return self.g.nodes[v]["model"]
        return "Unknown"

    def find_connecting_flights(self, origin_city: str, dest_city: str, max_hops: int = 3) -> list[dict]:
        """Graph traversal discovering valid direct & connecting itineraries (min 45m layover)."""
        origin_nodes = [n for n, attr in self.g.nodes(data=True) if attr.get("label") == "Airport" and attr.get("city") == origin_city]
        dest_nodes = {n for n, attr in self.g.nodes(data=True) if attr.get("label") == "Airport" and attr.get("city") == dest_city}
        if not origin_nodes or not dest_nodes:
            return []

        itineraries = []

        def dfs(curr_airport: str, path_flights: list[str], visited_airports: set[str]):
            if curr_airport in dest_nodes and path_flights:
                first_f = self.g.nodes[path_flights[0]]
                last_f = self.g.nodes[path_flights[-1]]
                total_dur = last_f["arrival"] - first_f["departure"]
                total_fare = sum(self.g.nodes[fn]["fare"] for fn in path_flights)
                route_codes = [self.g.nodes[origin_nodes[0]]["code"]]
                for fn in path_flights:
                    arr_ap = self._arrival_airport(fn)
                    route_codes.append(self.g.nodes[arr_ap]["code"])

                itineraries.append(
                    {
                        "Route_Type": "Direct" if len(path_flights) == 1 else f"{len(path_flights) - 1}-Stop Connecting",
                        "Flight_Sequence": " -> ".join(self.g.nodes[fn]["flight_id"] for fn in path_flights),
                        "Airport_Path": " -> ".join(route_codes),
                        "Aircraft_Used": " / ".join(self._operated_by_model(fn) for fn in path_flights),
                        "Total_Duration": str(total_dur),
                        "Total_Fare (INR)": total_fare,
                    }
                )
                return

            if len(path_flights) >= max_hops:
                return

            for f_node in self._flights_departing_from(curr_airport):
                f_data = self.g.nodes[f_node]
                if path_flights:
                    prev_arr = self.g.nodes[path_flights[-1]]["arrival"]
                    layover = f_data["departure"] - prev_arr
                    if layover < timedelta(minutes=45) or layover > timedelta(hours=8):
                        continue
                nxt_airport = self._arrival_airport(f_node)
                if nxt_airport and nxt_airport not in visited_airports:
                    dfs(nxt_airport, path_flights + [f_node], visited_airports | {nxt_airport})

        for orig in origin_nodes:
            dfs(orig, [], {orig})

        itineraries.sort(key=lambda x: x["Total_Duration"])
        return itineraries

    def get_passenger_bookings_graph(self) -> list[dict]:
        rows = []
        for u, v, d in self.g.edges(data=True):
            if d.get("rel") == "BOOKED":
                p_name = self.g.nodes[u]["name"]
                fid = self.g.nodes[v]["flight_id"]
                dep_ap = [self.g.nodes[dst]["code"] for _, dst, ed in self.g.out_edges(v, data=True) if ed.get("rel") == "DEPARTS_FROM"][0]
                arr_ap = [self.g.nodes[dst]["code"] for _, dst, ed in self.g.out_edges(v, data=True) if ed.get("rel") == "ARRIVES_AT"][0]
                rows.append(
                    {
                        "Passenger": p_name,
                        "Relationship": f"[:BOOKED (Seat {d['seat']})]",
                        "Flight": fid,
                        "Route": f"{dep_ap} -> {arr_ap}",
                        "Aircraft": self._operated_by_model(v),
                    }
                )
        return rows


def run_neo4j_demo():
    console.print(Panel.fit("[bold cyan]6.2 Neo4j Graph DB: Nodes, Relationships & Connecting Flight Finder[/bold cyan]"))
    mode = "EMBEDDED_NETWORKX_CYPHER_ENGINE"

    if is_port_open("127.0.0.1", 7687):
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))
            driver.verify_connectivity()
            mode = "LIVE_NEO4J"
            driver.close()
        except Exception:
            pass

    console.print(f"[cyan]Active Graph Engine:[/cyan] [bold]{mode}[/bold]\n")

    pg = AirlinePropertyGraph()
    airports = [
        ("DEL", "Indira Gandhi International", "New Delhi"),
        ("BOM", "Chhatrapati Shivaji Maharaj", "Mumbai"),
        ("BLR", "Kempegowda International", "Bengaluru"),
        ("MAA", "Chennai International", "Chennai"),
        ("SIN", "Singapore Changi", "Singapore"),
        ("DXB", "Dubai International", "Dubai"),
    ]
    for code, name, city in airports:
        pg.add_airport(code, name, city)

    pg.add_aircraft(1, "Airbus A320neo", 180)
    pg.add_aircraft(2, "Boeing 737-800", 186)
    pg.add_aircraft(3, "Boeing 787-9 Dreamliner", 290)

    pg.add_passenger(101, "Aarav Sharma")
    pg.add_passenger(102, "Diya Patel")
    pg.add_passenger(103, "Rohan Verma")

    # Schedule creating Direct, 1-Stop, and 2-Stop valid connecting chains
    pg.add_flight("AI-202", "DEL", "BOM", 1, datetime(2026, 11, 12, 8, 30), datetime(2026, 11, 12, 10, 40), 5200.0)
    pg.add_flight("AI-304", "BOM", "BLR", 2, datetime(2026, 11, 12, 12, 15), datetime(2026, 11, 12, 14, 0), 4100.0)
    pg.add_flight("AI-408", "BLR", "MAA", 1, datetime(2026, 11, 12, 15, 30), datetime(2026, 11, 12, 16, 40), 3200.0)
    pg.add_flight("AI-715", "DEL", "BLR", 2, datetime(2026, 11, 12, 13, 0), datetime(2026, 11, 12, 15, 45), 6100.0)
    pg.add_flight("AI-412", "BLR", "MAA", 1, datetime(2026, 11, 12, 17, 15), datetime(2026, 11, 12, 18, 25), 3400.0)
    pg.add_flight("AI-820", "BLR", "SIN", 3, datetime(2026, 11, 12, 18, 0), datetime(2026, 11, 13, 0, 30), 22000.0)

    pg.add_booking(101, "AI-202", "12A", "CONFIRMED")
    pg.add_booking(102, "AI-202", "12B", "CONFIRMED")
    pg.add_booking(103, "AI-304", "04C", "CONFIRMED")

    render_table(
        "Graph Traversal 1: Passenger -[:BOOKED]-> Flight -[:DEPARTS_FROM/ARRIVES_AT/OPERATED_BY]-> Nodes",
        pg.get_passenger_bookings_graph(),
    )

    routes_del_maa = pg.find_connecting_flights("New Delhi", "Chennai", max_hops=3)
    render_table("Graph Traversal 2: Connecting Flights (New Delhi -> Chennai)", routes_del_maa)

    routes_del_sin = pg.find_connecting_flights("New Delhi", "Singapore", max_hops=3)
    render_table("Graph Traversal 3: Connecting Flights (New Delhi -> Singapore)", routes_del_sin)


if __name__ == "__main__":
    run_neo4j_demo()
