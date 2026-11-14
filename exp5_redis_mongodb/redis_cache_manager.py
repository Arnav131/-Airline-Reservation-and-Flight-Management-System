"""
Experiment 5.1: Redis Key-Value Store Manager.
Handles:
  1. Passenger Sessions (TTL expiry)
  2. Frequently Searched Flight Cache (Cache Hit vs Cache Miss)
  3. Atomic Temporary Seat-Hold Lock (SET ... NX EX) with Real-Time Expiration
Dual-Mode: Connects to live Redis (localhost:6379) or embedded TTL-aware Redis Engine.
"""
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.config import REDIS_CONFIG, is_port_open
from db_core.relational_adapter import RelationalConnection, render_table

console = Console()


class EmbeddedRedisEngine:
    """High-fidelity Redis compatible store supporting TTL, SET NX EX, GET, DEL, KEYS."""

    def __init__(self):
        self._store: dict[str, tuple[str, Optional[float]]] = {}

    def _purge_if_expired(self, key: str) -> None:
        if key in self._store:
            _, exp = self._store[key]
            if exp is not None and time.time() >= exp:
                del self._store[key]

    def set(self, name: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        self._purge_if_expired(name)
        if nx and name in self._store:
            return False
        exp_ts = (time.time() + ex) if ex is not None else None
        self._store[name] = (str(value), exp_ts)
        return True

    def get(self, name: str) -> Optional[str]:
        self._purge_if_expired(name)
        entry = self._store.get(name)
        return entry[0] if entry else None

    def ttl(self, name: str) -> int:
        self._purge_if_expired(name)
        entry = self._store.get(name)
        if not entry:
            return -2
        if entry[1] is None:
            return -1
        return max(0, int(round(entry[1] - time.time())))

    def delete(self, *names: str) -> int:
        deleted = 0
        for name in names:
            if name in self._store:
                del self._store[name]
                deleted += 1
        return deleted

    def keys(self, pattern: str = "*") -> list[str]:
        now = time.time()
        for k in list(self._store.keys()):
            if self._store[k][1] is not None and now >= self._store[k][1]:
                del self._store[k]
        prefix = pattern.rstrip("*")
        return [k for k in self._store.keys() if k.startswith(prefix)]


def get_redis_client() -> tuple[Any, str]:
    if is_port_open(REDIS_CONFIG["host"], REDIS_CONFIG["port"]):
        try:
            import redis

            client = redis.Redis(decode_responses=True, **REDIS_CONFIG)
            client.ping()
            return client, "LIVE_REDIS"
        except Exception:
            pass
    return EmbeddedRedisEngine(), "EMBEDDED_REDIS"


def run_redis_demo():
    console.print(Panel.fit("[bold cyan]5.1 Redis: Sessions, Flight Search Cache & Atomic Seat-Hold Expiry[/bold cyan]"))
    r, mode = get_redis_client()
    console.print(f"[cyan]Active Redis Engine:[/cyan] [bold]{mode}[/bold]\n")

    # 1. Passenger Session Storage
    token = f"tok_{uuid.uuid4().hex[:8]}"
    session_payload = {"passenger_id": 101, "name": "Aarav Sharma", "tier": "Platinum", "login_hub": "DEL"}
    r.set(f"session:{token}", json.dumps(session_payload), ex=1800)
    retrieved_sess = json.loads(r.get(f"session:{token}"))
    console.print(f"[bold yellow]1. Session Stored:[/bold yellow] key=session:{token} | TTL={r.ttl(f'session:{token}')}s | Data={retrieved_sess}")

    # 2. Frequently Searched Flight Information Caching (Cache Miss vs Cache Hit)
    db = RelationalConnection()
    cache_key = "cache:flights:DEL:BOM"
    r.delete(cache_key)

    t0 = time.perf_counter()
    cached = r.get(cache_key)
    if not cached:
        # Cache Miss -> query relational DB
        flights = db.fetchall(
            "SELECT Flight_ID, Source_Airport, Destination_Airport, Departure_Time, Base_Fare FROM Flights WHERE Source_Airport='DEL' AND Destination_Airport='BOM'"
        )
        r.set(cache_key, json.dumps(flights), ex=300)
        miss_ms = (time.perf_counter() - t0) * 1000
    else:
        miss_ms = 0.0

    t1 = time.perf_counter()
    hit_data = json.loads(r.get(cache_key))
    hit_ms = (time.perf_counter() - t1) * 1000
    db.close()

    cache_metrics = [
        {"Lookup Mode": "Cache MISS (Relational DB Query + Populate)", "Latency (ms)": round(miss_ms, 4), "TTL (s)": r.ttl(cache_key), "Flights Found": len(hit_data)},
        {"Lookup Mode": "Cache HIT (In-Memory Redis Key-Value)", "Latency (ms)": round(hit_ms, 4), "TTL (s)": r.ttl(cache_key), "Flights Found": len(hit_data)},
    ]
    render_table("2. Redis Flight Search Cache Performance", cache_metrics)

    # 3. Temporary Seat-Hold with Atomic SET NX EX + Expiry Verification
    seat_key = "seat_hold:AI-202:19A"
    r.delete(seat_key)
    console.print("[bold yellow]3. Temporary Seat Hold (SET NX EX with 2-second TTL for live expiry verification):[/bold yellow]")
    p1_hold = r.set(seat_key, json.dumps({"passenger_id": 101, "status": "CHECKOUT_HOLD"}), ex=2, nx=True)
    p2_hold = r.set(seat_key, json.dumps({"passenger_id": 102, "status": "CHECKOUT_HOLD"}), ex=2, nx=True)
    console.print(f"   • Passenger 101 acquire hold on 19A: [green]{p1_hold}[/green] (TTL={r.ttl(seat_key)}s)")
    console.print(f"   • Passenger 102 concurrent hold attempt: [red]{p2_hold}[/red] (Blocked by atomic NX lock)")

    console.print("   [dim]⏳ Waiting 2.2 seconds for Redis TTL automatic expiration...[/dim]")
    time.sleep(2.2)

    after_expiry_state = r.get(seat_key)
    p2_retry = r.set(seat_key, json.dumps({"passenger_id": 102, "status": "CHECKOUT_HOLD"}), ex=600, nx=True)
    console.print(f"   • Key value after TTL expiry: [cyan]{after_expiry_state}[/cyan]")
    console.print(f"   • Passenger 102 retry after expiry: [green]{p2_retry}[/green] (Hold acquired cleanly!)\n")

    # Cleanup short-lived demo keys
    r.delete(seat_key, f"session:{token}", cache_key)


if __name__ == "__main__":
    run_redis_demo()
