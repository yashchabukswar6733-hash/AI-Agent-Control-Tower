from pathlib import Path
import sqlite3
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = "sqlite:///" + str(BASE_DIR / "saas.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ============================================================
# SQLALCHEMY SESSION
# ============================================================

def get_session():
    return SessionLocal()


# ============================================================
# LEGACY SQLITE COMPATIBILITY
#
# Existing application modules use:
#     with get_db() as db:
#         db.execute(...)
#
# Keep that interface working while we migrate modules
# gradually to SQLAlchemy.
# ============================================================

def get_db():
    connection = sqlite3.connect(
        BASE_DIR / "saas.db",
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    try:
        yield_or_return = connection

        class DBContext:
            def __enter__(self):
                return yield_or_return

            def __exit__(self, exc_type, exc_value, traceback):
                if exc_type is None:
                    yield_or_return.commit()
                else:
                    yield_or_return.rollback()

                yield_or_return.close()

        return DBContext()

    except Exception:
        connection.close()
        raise


# ============================================================
# HELPERS USED BY EXISTING APPLICATION
# ============================================================

def new_id():
    return uuid.uuid4().hex[:8]


def now():
    return datetime.utcnow().isoformat()


# ============================================================
# EXISTING DATABASE SCHEMA
#
# This preserves the tables already used by main.py.
# ============================================================

def init_db():

    db = sqlite3.connect(
        BASE_DIR / "saas.db",
        check_same_thread=False,
    )

    db.row_factory = sqlite3.Row

    cursor = db.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            agent TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            goal TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workflow_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT
        );

        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT DEFAULT '',
            business TEXT DEFAULT '',
            requirement TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            score INTEGER DEFAULT 0,
            ai_analysis TEXT DEFAULT '',
            follow_up TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sales_opportunities (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            stage TEXT DEFAULT 'new',
            service TEXT DEFAULT '',
            setup_fee REAL DEFAULT 0,
            monthly_fee REAL DEFAULT 0,
            probability INTEGER DEFAULT 10,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS revenue (
            id TEXT PRIMARY KEY,
            lead_id TEXT,
            client_id TEXT,
            service TEXT,
            setup_fee REAL DEFAULT 0,
            monthly_fee REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            payment_date TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY,
            lead_id TEXT,
            client_name TEXT NOT NULL,
            company TEXT NOT NULL,
            service TEXT NOT NULL,
            setup_fee REAL DEFAULT 0,
            monthly_fee REAL DEFAULT 0,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    db.commit()
    db.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()
