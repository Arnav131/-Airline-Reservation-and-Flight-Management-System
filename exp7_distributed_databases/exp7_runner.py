"""Experiment 7 Runner: Distributed Airport Database Cluster."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from exp7_distributed_databases.distributed_cluster_sim import DistributedAirportCluster
from exp7_distributed_databases.data_sharding_router import run_sharding_demo
from exp7_distributed_databases.schedule_replication_engine import replicate_schedules_across_cluster
from exp7_distributed_databases.eventual_consistency_demo import demonstrate_eventual_consistency

console = Console()


def run_experiment_7():
    console.print(Panel.fit("[bold green]EXPERIMENT 7: Distributed Airport Databases (Partitioning, Sharding, Replication, Eventual Consistency)[/bold green]"))
    cluster = DistributedAirportCluster()
    run_sharding_demo(cluster)
    replicate_schedules_across_cluster(cluster)
    demonstrate_eventual_consistency(cluster)


if __name__ == "__main__":
    run_experiment_7()
