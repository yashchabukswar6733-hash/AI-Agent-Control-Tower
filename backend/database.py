from pathlib import Path
import sqlite3
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "saas.db"

DATABASE_URL = (
    "sqlite:///"
    + str(DATABASE_PATH)
)


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_session():

    return SessionLocal()


def get_db():

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    class DBContext:

        def __enter__(self):

            return connection

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback
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


def init_db():

    db = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    db.row_factory = sqlite3.Row

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS client_onboarding
        (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            business_id TEXT NOT NULL,
            payment_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'started',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS client_delivery_tasks
        (
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

        CREATE INDEX IF NOT EXISTS
        idx_onboarding_business
        ON client_onboarding(business_id);

        CREATE INDEX IF NOT EXISTS
        idx_delivery_client
        ON client_delivery_tasks(client_id);

        CREATE INDEX IF NOT EXISTS
        idx_delivery_business
        ON client_delivery_tasks(business_id);

        CREATE INDEX IF NOT EXISTS
        idx_payments_razorpay_order
        ON payments(razorpay_order_id);
        """
    )

    db.commit()
    db.close()


init_db()
