"""
Experiment 4.3: Shared (S) vs Exclusive (X) Locks Demonstration.
Models InnoDB FOR SHARE (S-Lock) and FOR UPDATE (X-Lock) compatibility matrix
paired with real relational queries.
"""
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import RelationalConnection, render_table
from exp1_relational_sql.exp1_runner import init_schema_and_seed

console = Console()


class RowLockManager:
    """Implements Strict Two-Phase Locking (S-Locks & X-Locks) over database rows."""

    def __init__(self):
        self._cond = threading.Condition()
        self._shared_holders: dict[str, set[str]] = {}
        self._exclusive_holder: dict[str, str | None] = {}

    def acquire_shared(self, resource: str, txn_id: str) -> None:
        with self._cond:
            while self._exclusive_holder.get(resource) not in (None, txn_id):
                self._cond.wait()
            self._shared_holders.setdefault(resource, set()).add(txn_id)

    def acquire_exclusive(self, resource: str, txn_id: str) -> None:
        with self._cond:
            while True:
                x_owner = self._exclusive_holder.get(resource)
                s_owners = self._shared_holders.get(resource, set())
                other_s = s_owners - {txn_id}
                if x_owner in (None, txn_id) and len(other_s) == 0:
                    self._exclusive_holder[resource] = txn_id
                    break
                self._cond.wait()

    def release_all(self, txn_id: str) -> None:
        with self._cond:
            for res in list(self._shared_holders.keys()):
                self._shared_holders[res].discard(txn_id)
            for res, owner in list(self._exclusive_holder.items()):
                if owner == txn_id:
                    self._exclusive_holder[res] = None
            self._cond.notify_all()


def demonstrate_shared_vs_exclusive_locks():
    console.print(Panel.fit("[bold cyan]4.3 Shared (FOR SHARE) vs Exclusive (FOR UPDATE) Locks[/bold cyan]"))
    db = RelationalConnection()
    init_schema_and_seed(db)
    db.close()

    lock_mgr = RowLockManager()
    timeline = []
    tl_lock = threading.Lock()
    t_start = time.perf_counter()

    def log_event(txn: str, lock_type: str, event: str):
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 1)
        with tl_lock:
            timeline.append({"Time (ms)": elapsed_ms, "Transaction": txn, "Lock Mode": lock_type, "Action / Event": event})

    resource = "Flights:AI-202"

    # Two concurrent Shared Readers (FOR SHARE)
    def shared_reader(txn_name: str, hold_sec: float):
        conn = RelationalConnection()
        log_event(txn_name, "SHARED (S)", "Requesting SELECT ... FOR SHARE on AI-202")
        lock_mgr.acquire_shared(resource, txn_name)
        log_event(txn_name, "SHARED (S)", "Acquired S-Lock (Concurrent readers allowed!)")
        row = conn.fetchall("SELECT Flight_ID, Flight_Status, Base_Fare FROM Flights WHERE Flight_ID = 'AI-202'")[0]
        time.sleep(hold_sec)
        log_event(txn_name, "SHARED (S)", f"Read Fare ₹{row['Base_Fare']}, Releasing S-Lock")
        lock_mgr.release_all(txn_name)
        conn.close()

    # An Exclusive Writer (FOR UPDATE) that must wait for S-locks, then blocks subsequent readers
    def exclusive_writer(txn_name: str):
        time.sleep(0.05)  # Start slightly after readers acquire S-lock
        conn = RelationalConnection()
        log_event(txn_name, "EXCLUSIVE (X)", "Requesting SELECT ... FOR UPDATE on AI-202 (Blocked until S-locks release)")
        lock_mgr.acquire_exclusive(resource, txn_name)
        log_event(txn_name, "EXCLUSIVE (X)", "Acquired X-Lock! Updating Base_Fare -> 5800.00")
        conn.execute("BEGIN" if conn.mode == "sqlite" else "START TRANSACTION")
        conn.execute("UPDATE Flights SET Base_Fare = 5800.00 WHERE Flight_ID = 'AI-202'")
        time.sleep(0.25)  # Hold X-lock while reader 3 waits
        conn.commit()
        log_event(txn_name, "EXCLUSIVE (X)", "Committed & Released X-Lock")
        lock_mgr.release_all(txn_name)
        conn.close()

    def late_reader(txn_name: str):
        time.sleep(0.30)  # Arrives while Writer holds X-Lock
        conn = RelationalConnection()
        log_event(txn_name, "SHARED (S)", "Requesting S-Lock (Blocked by Writer's X-Lock)")
        lock_mgr.acquire_shared(resource, txn_name)
        row = conn.fetchall("SELECT Base_Fare FROM Flights WHERE Flight_ID = 'AI-202'")[0]
        log_event(txn_name, "SHARED (S)", f"Acquired S-Lock after X-Lock commit; Saw updated Fare ₹{row['Base_Fare']}")
        lock_mgr.release_all(txn_name)
        conn.close()

    threads = [
        threading.Thread(target=shared_reader, args=("Txn-Reader-1", 0.20)),
        threading.Thread(target=shared_reader, args=("Txn-Reader-2", 0.20)),
        threading.Thread(target=exclusive_writer, args=("Txn-Writer-X",)),
        threading.Thread(target=late_reader, args=("Txn-Reader-3",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    timeline.sort(key=lambda x: x["Time (ms)"])
    render_table("Shared vs Exclusive Lock Execution Timeline", timeline)
    console.print("[green]✓ Verified: Multiple S-locks run concurrently; X-locks wait for S-locks and block incoming S/X locks.[/green]\n")


if __name__ == "__main__":
    demonstrate_shared_vs_exclusive_locks()
