"""Experiment 4 Runner: Executes all 5 Transaction & Concurrency demonstrations."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from exp4_transaction_concurrency import (
    __name__ as _pkg,
)

console = Console()


def run_experiment_4():
    console.print(Panel.fit("[bold green]EXPERIMENT 4: Transaction Management, Locks, Deadlock & MVCC[/bold green]"))
    from exp4_transaction_concurrency import (
        __file__ as _,
    )
    import importlib

    m1 = importlib.import_module("exp4_transaction_concurrency.01_acid_demonstration")
    m2 = importlib.import_module("exp4_transaction_concurrency.02_race_condition_seat")
    m3 = importlib.import_module("exp4_transaction_concurrency.03_shared_exclusive_locks")
    m4 = importlib.import_module("exp4_transaction_concurrency.04_deadlock_simulation")
    m5 = importlib.import_module("exp4_transaction_concurrency.05_mvcc_investigation")

    m1.demonstrate_acid()
    m2.simulate_concurrent_seat_race()
    m3.demonstrate_shared_vs_exclusive_locks()
    m4.demonstrate_deadlock()
    m5.demonstrate_mvcc()


if __name__ == "__main__":
    run_experiment_4()
