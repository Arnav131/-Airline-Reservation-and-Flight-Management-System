import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.table import Table

from db_core.config import MYSQL_CONFIG, SQLITE_DB_PATH, is_port_open

console = Console()


def _sqlite_sha2(text: str, bits: int = 256) -> str:
    """Provide MySQL-compatible SHA2(text, bits) in SQLite."""
    if text is None:
        return ""
    data = str(text).encode("utf-8")
    if bits == 256:
        return hashlib.sha256(data).hexdigest()
    if bits == 512:
        return hashlib.sha512(data).hexdigest()
    return hashlib.sha256(data).hexdigest()


class RelationalConnection:
    """Dual-mode relational engine: connects to live MySQL 8.0 or embedded SQLite WAL engine."""

    def __init__(self, db_path: Path = SQLITE_DB_PATH, force_sqlite: bool = False):
        self.db_path = db_path
        self.mode = "sqlite"
        self.conn: Any = None

        if not force_sqlite and is_port_open(MYSQL_CONFIG["host"], MYSQL_CONFIG["port"]):
            try:
                import mysql.connector

                self.conn = mysql.connector.connect(
                    host=MYSQL_CONFIG["host"],
                    port=MYSQL_CONFIG["port"],
                    user=MYSQL_CONFIG["user"],
                    password=MYSQL_CONFIG["password"],
                    database=MYSQL_CONFIG["database"],
                    autocommit=False,
                )
                self.mode = "mysql"
            except Exception:
                self.mode = "sqlite"

        if self.mode == "sqlite":
            self.conn = sqlite3.connect(
                str(self.db_path),
                timeout=15.0,
                isolation_level=None,  # Explicit transaction control
                check_same_thread=False,
            )
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.execute("PRAGMA journal_mode = WAL;")
            self.conn.create_function("SHA2", 2, _sqlite_sha2)

    def cursor(self):
        return self.conn.cursor()

    def execute(self, sql: str, params: tuple = ()):
        cur = self.conn.cursor()
        if self.mode == "mysql":
            sql = sql.replace("?", "%s")
        cur.execute(sql, params)
        return cur

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        cur = self.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            return []
        if self.mode == "sqlite":
            return [dict(r) for r in rows]
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()


def render_table(title: str, rows: list[dict[str, Any]], max_rows: int = 25) -> None:
    """Pretty-print query result rows using Rich."""
    if not rows:
        console.print(f"[yellow]{title}: (0 rows)[/yellow]")
        return
    table = Table(title=title, show_header=True, header_style="bold cyan")
    headers = list(rows[0].keys())
    for h in headers:
        table.add_column(str(h))
    for r in rows[:max_rows]:
        table.add_row(*[str(r.get(h, "")) for h in headers])
    console.print(table)
    if len(rows) > max_rows:
        console.print(f"[dim]... showing {max_rows} of {len(rows)} rows[/dim]")
