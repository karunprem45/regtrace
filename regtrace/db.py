"""Database connection and schema. Same SQL runs on SQLite (tests, local) and PostgreSQL."""
import sqlite3

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS devices (
        k_number TEXT PRIMARY KEY,
        device_name TEXT,
        applicant TEXT,
        product_code TEXT,
        decision_date TEXT,
        decision TEXT,
        clearance_type TEXT,
        device_class TEXT,
        regulation_number TEXT,
        specialty TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS summary_pages (
        k_number TEXT NOT NULL,
        page INTEGER NOT NULL,
        text TEXT NOT NULL,
        PRIMARY KEY (k_number, page)
    )""",
    """CREATE TABLE IF NOT EXISTS predicates (
        k_number TEXT NOT NULL,
        predicate_k TEXT NOT NULL,
        page INTEGER,
        method TEXT NOT NULL,
        PRIMARY KEY (k_number, predicate_k, method)
    )""",
]


class DB:
    """Thin wrapper so the rest of the code does not care which driver is underneath."""

    def __init__(self, url: str):
        self.url = url
        if url.startswith(("postgresql://", "postgres://")):
            import psycopg  # only needed for Postgres

            self.conn = psycopg.connect(url)
            self.ph = "%s"
        else:
            path = url[len("sqlite:///"):] if url.startswith("sqlite:///") else url
            self.conn = sqlite3.connect(path, check_same_thread=False)
            self.ph = "?"

    def sql(self, query: str) -> str:
        return query.replace("?", self.ph)

    def execute(self, query: str, params=()):
        cur = self.conn.cursor()
        cur.execute(self.sql(query), params)
        return cur

    def executemany(self, query: str, rows):
        cur = self.conn.cursor()
        cur.executemany(self.sql(query), rows)
        return cur

    def init_schema(self):
        for stmt in SCHEMA:
            self.execute(stmt)
        self.conn.commit()

    def commit(self):
        self.conn.commit()
