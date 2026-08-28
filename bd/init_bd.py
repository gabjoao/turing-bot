import sqlite3
from pathlib import Path

DB_PATH = Path("data.db")
SCHEMA_PATH = Path("schema.sql")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
    conn.close()
    print(f"Banco criado em {DB_PATH.resolve()}")


if __name__ == "__main__":
    init_db()
