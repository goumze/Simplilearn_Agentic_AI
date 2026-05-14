"""
Database module for Banking Customer Support AI Agent.
Manages SQLite database for support tickets.
"""

import sqlite3
import os
import random
import logging
from datetime import datetime
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "support_tickets.db")

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and seed sample data if the database does not exist."""
    db_exists = Path(DB_PATH).exists()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS support_tickets (
            ticket_id     TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            issue         TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'Unresolved',
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT NOT NULL,
            user_message  TEXT NOT NULL,
            classification TEXT NOT NULL,
            agent_used    TEXT NOT NULL,
            response      TEXT NOT NULL,
            ticket_id     TEXT,
            success       INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    conn.commit()

    # Seed sample tickets only on first creation
    if not db_exists:
        sample_tickets = [
            ("650932", "Alice Johnson", "Net banking login failure", "Resolved"),
            ("784521", "Bob Smith", "Debit card replacement delayed", "In Progress"),
            ("123456", "Carol White", "UPI transaction failed", "Unresolved"),
            ("999001", "David Lee", "Credit card statement error", "Resolved"),
            ("555444", "Eve Davis", "Loan EMI deducted twice", "In Progress"),
        ]
        now = datetime.utcnow().isoformat()
        cursor.executemany(
            """
            INSERT OR IGNORE INTO support_tickets
                (ticket_id, customer_name, issue, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [(tid, name, issue, status, now, now) for tid, name, issue, status in sample_tickets],
        )
        conn.commit()
        logger.info("Database initialized with sample tickets.")
    else:
        logger.info("Database already exists, skipping seed.")

    conn.close()


def generate_ticket_id() -> str:
    """Generate a unique 6-digit ticket ID not already in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    while True:
        ticket_id = str(random.randint(100000, 999999))
        cursor.execute("SELECT 1 FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
        if cursor.fetchone() is None:
            conn.close()
            return ticket_id


def create_ticket(ticket_id: str, customer_name: str, issue: str) -> dict:
    """Insert a new unresolved ticket into the database."""
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO support_tickets (ticket_id, customer_name, issue, status, created_at, updated_at)
        VALUES (?, ?, ?, 'Unresolved', ?, ?)
        """,
        (ticket_id, customer_name, issue, now, now),
    )
    conn.commit()
    conn.close()
    return {"ticket_id": ticket_id, "customer_name": customer_name, "issue": issue, "status": "Unresolved"}


def get_ticket(ticket_id: str) -> dict | None:
    """Fetch a ticket by ID. Returns None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def log_interaction(
    user_message: str,
    classification: str,
    agent_used: str,
    response: str,
    ticket_id: str | None = None,
    success: bool = True,
) -> None:
    """Persist an agent interaction to the logs table."""
    now = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO agent_logs (timestamp, user_message, classification, agent_used, response, ticket_id, success)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (now, user_message, classification, agent_used, response, ticket_id, int(success)),
    )
    conn.commit()
    conn.close()


def get_all_logs() -> list[dict]:
    """Return all agent interaction logs ordered by most recent first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_tickets() -> list[dict]:
    """Return all support tickets ordered by most recent first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM support_tickets ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print(f"Database initialized at: {DB_PATH}")
