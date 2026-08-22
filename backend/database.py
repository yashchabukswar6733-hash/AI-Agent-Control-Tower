from pathlib import Path
import sqlite3
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "saas.db"

DATABASE_URL = "sqlite:///" + str(DATABASE_PATH)


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


def get_session():
    return SessionLocal()


def get_db():

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    class DBContext:

        def __enter__(self):
            return connection

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):

            if exc_type is None:
                connection.commit()
            else:
                connection.rollback()

            connection.close()

    return DBContext()


def new_id():
    return uuid.uuid4().hex[:8]


def now():
    return datetime.utcnow().isoformat()


def table_exists(db, table_name):

    row = db.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def add_column_if_missing(
    db,
    table,
    column,
    definition,
):

    if not table_exists(db, table):
        return

    columns = {
        row["name"]
        for row in db.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }

    if column not in columns:

        db.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {definition}
            """
        )


def init_db():

    db = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )

    db.row_factory = sqlite3.Row

    try:

        # ====================================================
        # CORE TABLES
        # ====================================================

        db.executescript(
            """

            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                business_id TEXT,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                updated_at TEXT
            );


            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                business_id TEXT
            );


            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                agent TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at TEXT NOT NULL,
                business_id TEXT
            );


            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                goal TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at TEXT NOT NULL,
                business_id TEXT
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
                updated_at TEXT NOT NULL,
                business_id TEXT
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
                updated_at TEXT NOT NULL,
                business_id TEXT
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
                created_at TEXT NOT NULL,
                business_id TEXT
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
                updated_at TEXT NOT NULL,
                business_id TEXT
            );


            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                proposal_id TEXT,
                client_id TEXT,
                business_id TEXT,
                client_name TEXT NOT NULL,
                company TEXT NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                payment_type TEXT NOT NULL DEFAULT 'setup',
                status TEXT NOT NULL DEFAULT 'pending',
                payment_date TEXT,
                razorpay_order_id TEXT,
                razorpay_payment_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            );


            CREATE TABLE IF NOT EXISTS client_onboarding (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                payment_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'started',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );


            CREATE TABLE IF NOT EXISTS client_delivery_tasks (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                onboarding_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                position INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            """
        )

        # ====================================================
        # SAFE MIGRATIONS
        # ====================================================

        add_column_if_missing(
            db,
            "payments",
            "razorpay_order_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "payments",
            "razorpay_payment_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "payments",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "payments",
            "updated_at",
            "TEXT",
        )


        add_column_if_missing(
            db,
            "clients",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "clients",
            "email",
            "TEXT DEFAULT ''",
        )

        add_column_if_missing(
            db,
            "clients",
            "phone",
            "TEXT DEFAULT ''",
        )

        add_column_if_missing(
            db,
            "clients",
            "updated_at",
            "TEXT",
        )


        add_column_if_missing(
            db,
            "agents",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "tasks",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "workflows",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "leads",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "sales_opportunities",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "revenue",
            "business_id",
            "TEXT",
        )

        add_column_if_missing(
            db,
            "proposals",
            "business_id",
            "TEXT",
        )


        # ====================================================
        # INDEXES
        #
        # Created only AFTER payments definitely exists.
        # ====================================================

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_onboarding_business
            ON client_onboarding(business_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_delivery_client
            ON client_delivery_tasks(client_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_delivery_business
            ON client_delivery_tasks(business_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_payments_razorpay_order
            ON payments(razorpay_order_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_payments_business
            ON payments(business_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_leads_business
            ON leads(business_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_clients_business
            ON clients(business_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_proposals_business
            ON proposals(business_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_revenue_business
            ON revenue(business_id)
            """
        )


        db.commit()

    finally:

        db.close()


init_db()