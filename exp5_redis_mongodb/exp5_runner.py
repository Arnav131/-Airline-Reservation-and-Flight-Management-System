"""Experiment 5 Runner: Redis & MongoDB Multi-Model Polyglot Store."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from exp5_redis_mongodb.redis_cache_manager import run_redis_demo
from exp5_redis_mongodb.mongo_document_manager import seed_and_run_crud
from exp5_redis_mongodb.mongo_aggregation_analytics import run_mongo_aggregation

console = Console()


def run_experiment_5():
    console.print(Panel.fit("[bold green]EXPERIMENT 5: Redis (Cache & Seat Holds) + MongoDB (Documents & Aggregation)[/bold green]"))
    run_redis_demo()
    seed_and_run_crud()
    run_mongo_aggregation()


if __name__ == "__main__":
    run_experiment_5()
