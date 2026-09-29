"""Real SQLite-backed storage (stdlib sqlite3, no ORM -- this app is
small enough that one didn't earn its weight) instead of a hardcoded
Python list, so an inline edit (see main.py's toggle-sponsorship route)
actually persists rather than only mutating an in-process constant."""

import sqlite3

_SEED = [
    ("Acme Analytics", "Software", 1),
    ("Northwind Foods", "Consumer", 0),
    ("Contoso Cloud", "Software", 1),
    ("BlueRiver Health", "Healthcare", 0),
    ("Fabrikam Robotics", "Manufacturing", 1),
    ("Globex Financial", "Finance", 1),
    ("Initech Systems", "Software", 0),
    ("Umbrella Biotech", "Healthcare", 1),
]

# A single shared in-memory connection for the whole process -- SQLite's
# :memory: database only exists per-connection, so this has to be one
# connection reused across requests, not a fresh one opened per call.
# check_same_thread=False since FastAPI's sync route functions can run on
# a worker thread different from the one that opened this connection.
_conn = sqlite3.connect(":memory:", check_same_thread=False)
_conn.row_factory = sqlite3.Row


def init_db() -> None:
    # Deliberately plain INTEGER PRIMARY KEY, not AUTOINCREMENT: the
    # AUTOINCREMENT keyword tracks a persistent high-water mark in
    # sqlite_sequence that survives a DELETE, so reset_db() would hand out
    # ever-growing ids across resets instead of a stable, predictable
    # 1..8 each time -- which is what both the seed data and the tests
    # below rely on.
    _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            industry TEXT NOT NULL,
            sponsors_h1b INTEGER NOT NULL
        )
        """
    )
    if _conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 0:
        reset_db()


def reset_db() -> None:
    """Clears and re-seeds the table -- used at startup and between tests
    so each test runs against known, independent data regardless of what
    an earlier test's inline edit changed."""
    _conn.execute("DELETE FROM companies")
    _conn.executemany(
        "INSERT INTO companies (name, industry, sponsors_h1b) VALUES (?, ?, ?)",
        _SEED,
    )
    _conn.commit()


def search_companies(query: str) -> list[dict]:
    query = query.strip().lower()
    if not query:
        rows = _conn.execute("SELECT * FROM companies ORDER BY name").fetchall()
    else:
        like = f"%{query}%"
        rows = _conn.execute(
            "SELECT * FROM companies WHERE lower(name) LIKE ? OR lower(industry) LIKE ? ORDER BY name",
            (like, like),
        ).fetchall()
    return [dict(row) for row in rows]


def get_company(company_id: int) -> dict | None:
    row = _conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    return dict(row) if row else None


def toggle_sponsorship(company_id: int) -> dict | None:
    company = get_company(company_id)
    if company is None:
        return None
    new_value = 0 if company["sponsors_h1b"] else 1
    _conn.execute("UPDATE companies SET sponsors_h1b = ? WHERE id = ?", (new_value, company_id))
    _conn.commit()
    return get_company(company_id)
