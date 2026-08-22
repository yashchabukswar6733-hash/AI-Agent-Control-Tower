import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"


def now():
    return datetime.utcnow().isoformat()


def new_id():
    return uuid.uuid4().hex[:12]


def create_lead(
    name,
    phone="",
    email="",
    business="",
    requirement="",
    source="website",
    business_id=None,
):
    name = str(name or "").strip()
    phone = str(phone or "").strip()
    email = str(email or "").strip()
    business = str(business or "").strip()
    requirement = str(requirement or "").strip()
    source = str(source or "website").strip()

    if not name:
        raise ValueError("Lead name is required.")

    if not phone and not email:
        raise ValueError("Phone or email is required.")

    if not business_id:
        raise ValueError("Business ID is required.")

    lead_id = new_id()
    timestamp = now()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        # Verify tenant/business exists.
        business_row = db.execute(
            """
            SELECT id, business_name, active
            FROM businesses
            WHERE id = ?
            LIMIT 1
            """,
            (business_id,),
        ).fetchone()

        if not business_row:
            raise ValueError("Business not found.")

        if "active" in business_row.keys():
            if business_row["active"] in (0, "0", False):
                raise ValueError("Business is inactive.")

        # Create the real lead.
        db.execute(
            """
            INSERT INTO leads (
                id,
                name,
                phone,
                email,
                business,
                requirement,
                status,
                score,
                ai_analysis,
                follow_up,
                created_at,
                updated_at,
                business_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                name,
                phone,
                email,
                business or business_row["business_name"],
                requirement,
                "new",
                0,
                "",
                "",
                timestamp,
                timestamp,
                business_id,
            ),
        )

        # Create the sales opportunity automatically.
        opportunity_id = new_id()

        db.execute(
            """
            INSERT INTO sales_opportunities (
                id,
                lead_id,
                stage,
                service,
                setup_fee,
                monthly_fee,
                probability,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity_id,
                lead_id,
                "new",
                "",
                0,
                0,
                10,
                f"Lead source: {source}",
                timestamp,
                timestamp,
            ),
        )

        # Record the activity.
        db.execute(
            """
            INSERT INTO activity_log (
                entity_type,
                entity_id,
                action,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "lead",
                lead_id,
                "lead_created",
                f"source={source}; business_id={business_id}",
                timestamp,
            ),
        )

        db.commit()

        row = db.execute(
            """
            SELECT *
            FROM leads
            WHERE id = ?
            LIMIT 1
            """,
            (lead_id,),
        ).fetchone()

        return dict(row)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def list_leads(business_id):
    if not business_id:
        raise ValueError("Business ID is required.")

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        rows = db.execute(
            """
            SELECT
                l.*,
                so.stage AS opportunity_stage,
                so.probability AS opportunity_probability
            FROM leads l
            LEFT JOIN sales_opportunities so
                ON so.lead_id = l.id
            WHERE l.business_id = ?
            ORDER BY l.created_at DESC
            """,
            (business_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        db.close()
