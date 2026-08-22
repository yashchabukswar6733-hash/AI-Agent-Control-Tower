from .database import get_db

def init_business_auth():

    with get_db() as db:

        db.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            plan TEXT NOT NULL DEFAULT 'Starter',
            status TEXT NOT NULL DEFAULT 'trial',
            created_at TEXT NOT NULL
        )
        """)

        db.execute("""
        CREATE TABLE IF NOT EXISTS business_sessions (
            token TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
        """)

        db.execute("""
        CREATE INDEX IF NOT EXISTS idx_business_sessions_business
        ON business_sessions(business_id)
        """)

        db.execute("""
        CREATE INDEX IF NOT EXISTS idx_business_email
        ON businesses(email)
        """)
