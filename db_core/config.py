import os
import socket
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB_PATH = DATA_DIR / "iarfms.db"

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "iarfms_user"),
    "password": os.getenv("MYSQL_PASSWORD", "iarfms_password"),
    "database": os.getenv("MYSQL_DATABASE", "iarfms_db"),
}

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "127.0.0.1"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
}

MONGO_CONFIG = {
    "uri": os.getenv("MONGO_URI", "mongodb://admin:admin_password@127.0.0.1:27017/"),
    "database": os.getenv("MONGO_DB", "iarfms_nosql"),
}

CASSANDRA_CONFIG = {
    "hosts": [os.getenv("CASSANDRA_HOST", "127.0.0.1")],
    "port": int(os.getenv("CASSANDRA_PORT", "9042")),
    "keyspace": os.getenv("CASSANDRA_KEYSPACE", "airline_telemetry"),
}

NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687"),
    "user": os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "neo4j_password"),
}


def is_port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    """Quick non-blocking socket check to determine if a live database service is running."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def get_system_status() -> dict[str, bool]:
    """Return reachability status for all 5 database engines."""
    return {
        "mysql": is_port_open(MYSQL_CONFIG["host"], MYSQL_CONFIG["port"]),
        "redis": is_port_open(REDIS_CONFIG["host"], REDIS_CONFIG["port"]),
        "mongodb": is_port_open("127.0.0.1", 27017),
        "cassandra": is_port_open(CASSANDRA_CONFIG["hosts"][0], CASSANDRA_CONFIG["port"]),
        "neo4j": is_port_open("127.0.0.1", 7687),
    }
