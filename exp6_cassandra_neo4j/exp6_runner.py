"""Experiment 6 Runner: Apache Cassandra (Wide-Column) & Neo4j (Graph)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from exp6_cassandra_neo4j.cassandra_telemetry_runner import run_cassandra_demo
from exp6_cassandra_neo4j.neo4j_pathfinder import run_neo4j_demo

console = Console()


def run_experiment_6():
    console.print(Panel.fit("[bold green]EXPERIMENT 6: Cassandra (Time-Series Partitioning) + Neo4j (Graph Routing)[/bold green]"))
    run_cassandra_demo()
    run_neo4j_demo()


if __name__ == "__main__":
    run_experiment_6()
