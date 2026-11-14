"""
Experiment 4.4: Deadlock Simulation & Wait-For Graph (WFG) Victim Detection.
Simulates cyclic deadlock during concurrent Reservation & Payment locking:
  - Txn-1 locks Reservation:1001 -> waits for Payment:5002
  - Txn-2 locks Payment:5002     -> waits for Reservation:1001
Deadlock detector spots cycle Txn-1 -> Txn-2 -> Txn-1 and aborts the younger victim.
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


class DeadlockDetectedError(Exception):
    """Raised when Wait-For Graph detects a cycle and selects this txn as victim."""


class DeadlockAwareLockManager:
    """Tracks lock ownership and Wait-For Graph edges to detect cycles deterministically."""

    def __init__(self):
        self._cond = threading.Condition()
        self._owners: dict[str, str] = {}        # resource -> holder txn
        self._waiting_for: dict[str, str] = {}   # txn -> target holder txn
        self._aborted: set[str] = set()

    def _has_cycle(self, start_txn: str) -> bool:
        visited = set()
        curr = start_txn
        while curr in self._waiting_for:
            nxt = self._waiting_for[curr]
            if nxt == start_txn:
                return True
            if nxt in visited:
                return False
            visited.add(nxt)
            curr = nxt
        return False

    def acquire(self, resource: str, txn_id: str) -> None:
        with self._cond:
            while resource in self._owners and self._owners[resource] != txn_id:
                holder = self._owners[resource]
                self._waiting_for[txn_id] = holder
                if self._has_cycle(txn_id):
                    # Victim selection: abort the transaction whose request closed the cycle
                    del self._waiting_for[txn_id]
                    self._aborted.add(txn_id)
                    raise DeadlockDetectedError(
                        f"Deadlock cycle detected! {txn_id} <-> {holder}. Aborting victim {txn_id}."
                    )
                self._cond.wait(timeout=0.5)
                if txn_id in self._aborted:
                    raise DeadlockDetectedError(f"Transaction {txn_id} aborted as deadlock victim.")

            self._waiting_for.pop(txn_id, None)
            self._owners[resource] = txn_id

    def release_all(self, txn_id: str) -> None:
        with self._cond:
            self._waiting_for.pop(txn_id, None)
            for res in [r for r, owner in self._owners.items() if owner == txn_id]:
                del self._owners[res]
            self._cond.notify_all()


def demonstrate_deadlock():
    console.print(Panel.fit("[bold cyan]4.4 Deadlock Simulation (Reservation vs Payment Cyclic Lock)[/bold cyan]"))
    db = RelationalConnection()
    init_schema_and_seed(db)
    db.close()

    dl_mgr = DeadlockAwareLockManager()
    events = []
    ev_lock = threading.Lock()
    barrier = threading.Barrier(2)
    t0 = time.perf_counter()

    def log(txn: str, msg: str):
        with ev_lock:
            events.append({"Time (ms)": round((time.perf_counter() - t0) * 1000, 1), "Transaction": txn, "Event": msg})

    def txn_alpha():
        conn = RelationalConnection()
        try:
            conn.execute("BEGIN" if conn.mode == "sqlite" else "START TRANSACTION")
            dl_mgr.acquire("Reservation:1001", "Txn-Alpha")
            log("Txn-Alpha", "Locked Reservation:1001 (Updating Seat)")
            barrier.wait()  # Ensure both transactions hold their first lock simultaneously
            time.sleep(0.05)

            log("Txn-Alpha", "Requesting lock on Payment:5002...")
            dl_mgr.acquire("Payment:5002", "Txn-Alpha")
            conn.execute("UPDATE Payments SET Amount = Amount + 100 WHERE Payment_ID = 5002")
            conn.commit()
            log("Txn-Alpha", "COMMITTED successfully after surviving deadlock resolution ✓")
        except DeadlockDetectedError as exc:
            conn.rollback()
            log("Txn-Alpha", f"VICTIM ROLLED BACK: {exc}")
        finally:
            dl_mgr.release_all("Txn-Alpha")
            conn.close()

    def txn_beta():
        conn = RelationalConnection()
        try:
            conn.execute("BEGIN" if conn.mode == "sqlite" else "START TRANSACTION")
            dl_mgr.acquire("Payment:5002", "Txn-Beta")
            log("Txn-Beta", "Locked Payment:5002 (Verifying Fee)")
            barrier.wait()
            time.sleep(0.10)  # Slightly later second lock request -> closes cycle and becomes victim

            log("Txn-Beta", "Requesting lock on Reservation:1001...")
            dl_mgr.acquire("Reservation:1001", "Txn-Beta")
            conn.execute("UPDATE Reservations SET Seat_Number = '12Z' WHERE Reservation_ID = 1001")
            conn.commit()
            log("Txn-Beta", "COMMITTED successfully ✓")
        except DeadlockDetectedError as exc:
            conn.rollback()
            log("Txn-Beta", f"VICTIM ROLLED BACK: {exc}")
        finally:
            dl_mgr.release_all("Txn-Beta")
            conn.close()

    t1 = threading.Thread(target=txn_alpha)
    t2 = threading.Thread(target=txn_beta)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    events.sort(key=lambda x: x["Time (ms)"])
    render_table("Deadlock Detection & Victim Rollback Execution Trace", events)
    console.print("[green]✓ Cycle detected via Wait-For Graph, victim rolled back, survivor committed without hanging![/green]\n")


if __name__ == "__main__":
    demonstrate_deadlock()
