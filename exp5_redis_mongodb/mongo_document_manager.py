"""
Experiment 5.2: MongoDB Document Store Manager (Preferences, Baggage, Travel History & Flexible Bookings).
Dual-Mode: Connects to live MongoDB (localhost:27017) or embedded Mongo Document Engine.
"""
import copy
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.config import MONGO_CONFIG, is_port_open
from db_core.relational_adapter import render_table

console = Console()


class EmbeddedMongoCollection:
    """High-fidelity MongoDB collection supporting CRUD + Aggregation Pipelines."""

    def __init__(self, name: str):
        self.name = name
        self._docs: list[dict[str, Any]] = []
        self._seq = 1

    def drop(self) -> None:
        self._docs.clear()
        self._seq = 1

    def insert_one(self, doc: dict[str, Any]) -> dict[str, Any]:
        d = copy.deepcopy(doc)
        if "_id" not in d:
            d["_id"] = f"obj_{self._seq}"
            self._seq += 1
        self._docs.append(d)
        return {"inserted_id": d["_id"]}

    def insert_many(self, docs: list[dict[str, Any]]) -> list[Any]:
        return [self.insert_one(d)["inserted_id"] for d in docs]

    @staticmethod
    def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
        for key, expected in query.items():
            parts = key.split(".")
            val: Any = doc
            for p in parts:
                if isinstance(val, dict) and p in val:
                    val = val[p]
                else:
                    val = None
                    break
            if isinstance(expected, dict):
                for op, target in expected.items():
                    if op == "$gt" and not (val is not None and val > target):
                        return False
                    if op == "$gte" and not (val is not None and val >= target):
                        return False
                    if op == "$in" and val not in target:
                        return False
            else:
                if val != expected:
                    return False
        return True

    def find(self, query: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        q = query or {}
        return [copy.deepcopy(d) for d in self._docs if self._matches(d, q)]

    def find_one(self, query: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
        matches = self.find(query)
        return matches[0] if matches else None

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> int:
        for d in self._docs:
            if self._matches(d, query):
                if "$set" in update:
                    for k, v in update["$set"].items():
                        parts = k.split(".")
                        target = d
                        for p in parts[:-1]:
                            target = target.setdefault(p, {})
                        target[parts[-1]] = copy.deepcopy(v)
                if "$push" in update:
                    for k, v in update["$push"].items():
                        d.setdefault(k, []).append(copy.deepcopy(v))
                return 1
        return 0

    def delete_one(self, query: dict[str, Any]) -> int:
        for idx, d in enumerate(self._docs):
            if self._matches(d, query):
                del self._docs[idx]
                return 1
        return 0

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        docs = [copy.deepcopy(d) for d in self._docs]
        for stage in pipeline:
            if "$match" in stage:
                docs = [d for d in docs if self._matches(d, stage["$match"])]
            elif "$group" in stage:
                spec = stage["$group"]
                group_key_expr = spec["_id"]
                buckets: dict[Any, list[dict[str, Any]]] = defaultdict(list)
                for d in docs:
                    if isinstance(group_key_expr, str) and group_key_expr.startswith("$"):
                        g_key = self._extract_field(d, group_key_expr[1:])
                    else:
                        g_key = group_key_expr
                    buckets[g_key].append(d)

                grouped_results = []
                for g_key, items in buckets.items():
                    row: dict[str, Any] = {"_id": g_key}
                    for field, agg_expr in spec.items():
                        if field == "_id":
                            continue
                        op, arg = next(iter(agg_expr.items()))
                        if op == "$sum":
                            if arg == 1:
                                row[field] = len(items)
                            elif isinstance(arg, str) and arg.startswith("$"):
                                row[field] = round(sum(float(self._extract_field(it, arg[1:]) or 0) for it in items), 2)
                        elif op == "$avg":
                            vals = [float(self._extract_field(it, arg[1:]) or 0) for it in items]
                            row[field] = round(sum(vals) / len(vals), 2) if vals else 0.0
                        elif op == "$addToSet":
                            row[field] = sorted({str(self._extract_field(it, arg[1:])) for it in items})
                    grouped_results.append(row)
                docs = grouped_results
            elif "$sort" in stage:
                for k, direction in reversed(list(stage["$sort"].items())):
                    docs.sort(key=lambda x: x.get(k, 0), reverse=(direction == -1))
        return docs

    @staticmethod
    def _extract_field(doc: dict[str, Any], path: str) -> Any:
        val: Any = doc
        for part in path.split("."):
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return None
        return val


class EmbeddedMongoDatabase:
    def __init__(self):
        self._cols: dict[str, EmbeddedMongoCollection] = {}

    def __getitem__(self, name: str) -> EmbeddedMongoCollection:
        if name not in self._cols:
            self._cols[name] = EmbeddedMongoCollection(name)
        return self._cols[name]


_SHARED_EMBEDDED_MONGO = EmbeddedMongoDatabase()


def get_mongo_db() -> tuple[Any, str]:
    if is_port_open("127.0.0.1", 27017):
        try:
            from pymongo import MongoClient

            client = MongoClient(MONGO_CONFIG["uri"], serverSelectionTimeoutMS=1000)
            client.admin.command("ping")
            return client[MONGO_CONFIG["database"]], "LIVE_MONGODB"
        except Exception:
            pass
    return _SHARED_EMBEDDED_MONGO, "EMBEDDED_MONGODB"


def seed_and_run_crud():
    console.print(Panel.fit("[bold cyan]5.2 MongoDB: Flexible Booking Documents, Preferences, Baggage & CRUD[/bold cyan]"))
    mdb, mode = get_mongo_db()
    console.print(f"[cyan]Active MongoDB Engine:[/cyan] [bold]{mode}[/bold]\n")

    bookings_col = mdb["passenger_bookings"]
    bookings_col.drop()

    # CREATE (Insert flexible polyglot documents combining Preferences, Baggage, History)
    sample_docs = [
        {
            "reservation_id": 1001,
            "passenger_id": 101,
            "passenger_name": "Aarav Sharma",
            "flight_id": "AI-202",
            "route": "DEL -> BOM",
            "booking_status": "CONFIRMED",
            "fare_paid": 5200.0,
            "preferences": {"meal": "Vegan", "seat_zone": "Window", "wheelchair": False, "loyalty_tier": "Platinum"},
            "baggage": {"bags_count": 2, "total_weight_kg": 24.5, "tags": ["BG-881", "BG-882"], "status": "CHECKED_IN"},
            "travel_history": [{"flight": "AI-101", "date": "2026-08-14"}, {"flight": "AI-302", "date": "2026-09-21"}],
        },
        {
            "reservation_id": 1002,
            "passenger_id": 102,
            "passenger_name": "Diya Patel",
            "flight_id": "AI-202",
            "route": "DEL -> BOM",
            "booking_status": "CONFIRMED",
            "fare_paid": 5200.0,
            "preferences": {"meal": "Standard Veg", "seat_zone": "Aisle", "loyalty_tier": "Gold"},
            "baggage": {"bags_count": 1, "total_weight_kg": 15.0, "tags": ["BG-890"], "status": "LOADED"},
            "travel_history": [{"flight": "AI-202", "date": "2026-07-02"}],
        },
        {
            "reservation_id": 1003,
            "passenger_id": 103,
            "passenger_name": "Rohan Verma",
            "flight_id": "AI-304",
            "route": "BOM -> BLR",
            "booking_status": "CONFIRMED",
            "fare_paid": 4100.0,
            "preferences": {"meal": "Non-Veg", "seat_zone": "Window", "loyalty_tier": "Silver"},
            "baggage": {"bags_count": 1, "total_weight_kg": 18.2, "tags": ["BG-901"], "status": "LOADED"},
            "travel_history": [],
        },
        {
            "reservation_id": 1004,
            "passenger_id": 104,
            "passenger_name": "Ananya Iyer",
            "flight_id": "AI-510",
            "route": "DEL -> DXB",
            "booking_status": "CONFIRMED",
            "fare_paid": 40700.0,
            "preferences": {"meal": "Jain", "seat_zone": "First Suite", "loyalty_tier": "Platinum"},
            "baggage": {"bags_count": 3, "total_weight_kg": 42.0, "tags": ["BG-910", "BG-911", "BG-912"], "status": "SECURITY_CLEARED"},
            "travel_history": [{"flight": "AI-510", "date": "2026-05-19"}],
        },
        {
            "reservation_id": 1006,
            "passenger_id": 106,
            "passenger_name": "Meera Nair",
            "flight_id": "AI-202",
            "route": "DEL -> BOM",
            "booking_status": "CANCELLED",
            "fare_paid": 0.0,
            "preferences": {"meal": "Vegan", "seat_zone": "Middle", "loyalty_tier": "Bronze"},
            "baggage": {"bags_count": 0, "total_weight_kg": 0.0, "tags": [], "status": "NONE"},
            "travel_history": [],
        },
    ]
    bookings_col.insert_many(sample_docs)
    console.print(f"[green]✓ CREATE: Inserted {len(sample_docs)} flexible booking documents.[/green]")

    # READ (Query nested preference field)
    platinum_flyers = list(bookings_col.find({"preferences.loyalty_tier": "Platinum"}))
    read_rows = [
        {
            "Passenger": d["passenger_name"],
            "Flight": d["flight_id"],
            "Meal": d["preferences"]["meal"],
            "Bags": d["baggage"]["bags_count"],
            "Weight (kg)": d["baggage"]["total_weight_kg"],
            "Bag Status": d["baggage"]["status"],
        }
        for d in platinum_flyers
    ]
    render_table("READ: Query Nested Document Field (preferences.loyalty_tier == 'Platinum')", read_rows)

    # UPDATE (Update baggage status & append a travel history note)
    bookings_col.update_one(
        {"reservation_id": 1001},
        {
            "$set": {"baggage.status": "LOADED_ON_AIRCRAFT", "baggage.carousel": "DEL-T3-B2"},
            "$push": {"travel_history": {"flight": "AI-202", "date": "2026-11-12"}},
        },
    )
    updated_doc = bookings_col.find_one({"reservation_id": 1001})
    console.print(
        f"[yellow]✓ UPDATE: Passenger 101 baggage updated -> status={updated_doc['baggage']['status']}, "
        f"history_count={len(updated_doc['travel_history'])}[/yellow]"
    )

    # DELETE (Remove cancelled document for cleanup)
    del_res = bookings_col.delete_one({"booking_status": "CANCELLED"})
    deleted_count = del_res.deleted_count if hasattr(del_res, "deleted_count") else del_res
    console.print(f"[red]✓ DELETE: Purged {deleted_count} CANCELLED flexible booking document(s).[/red]\n")


if __name__ == "__main__":
    seed_and_run_crud()
