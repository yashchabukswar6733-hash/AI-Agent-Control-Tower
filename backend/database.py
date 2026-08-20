import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "control_tower.db"


def new_id():
    return uuid.uuid4().hex[:8]


def now():
    return datetime.now().isoformat()


@contextmanager
def get_db():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def init_db():

    with get_db() as db:

        # ---------------- CLIENTS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ---------------- AGENTS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ---------------- TASKS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # ---------------- WORKFLOWS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                goal TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # ---------------- WORKFLOW STEPS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS workflow_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT
            )
        """)

        # ---------------- LEADS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                business TEXT,
                requirement TEXT,
                status TEXT NOT NULL,
                score INTEGER,
                ai_analysis TEXT,
                follow_up TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)

        # ---------------- LEADS MIGRATION ----------------
        # Adds updated_at to old databases that were created
        # before this column existed.

        lead_columns = db.execute(
            "PRAGMA table_info(leads)"
        ).fetchall()

        lead_column_names = [
            column["name"] for column in lead_columns
        ]

        if "updated_at" not in lead_column_names:

            db.execute(
                "ALTER TABLE leads ADD COLUMN updated_at TEXT"
            )

            db.execute(
                """
                UPDATE leads
                SET updated_at = created_at
                WHERE updated_at IS NULL
                """
            )

        # ---------------- PROPOSALS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                lead_id TEXT,
                client_name TEXT NOT NULL,
                company TEXT NOT NULL,
                service TEXT NOT NULL,
                setup_fee REAL NOT NULL,
                monthly_fee REAL NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ---------------- PAYMENTS ----------------

        db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                client_name TEXT NOT NULL,
                company TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ---------------- DEFAULT AGENT ----------------

        existing_agent = db.execute(
            "SELECT id FROM agents LIMIT 1"
        ).fetchone()

        if not existing_agent:

            db.execute(
                """
                INSERT INTO agents
                (id, name, role, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    new_id(),
                    "Research Agent",
                    "Research",
                    "active",
                    now()
                )
            )