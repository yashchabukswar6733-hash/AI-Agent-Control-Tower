import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "saas.db"


def qualify_lead(lead_id):
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    try:
        lead = db.execute(
            """
            SELECT *
            FROM leads
            WHERE id = ?
            LIMIT 1
            """,
            (lead_id,),
        ).fetchone()

        if not lead:
            raise ValueError("Lead not found.")

        requirement = (lead["requirement"] or "").lower()

        # Real deterministic qualification.
        # AI provider can be connected later through the existing AI service.
        score = 30

        buying_signals = [
            "price",
            "pricing",
            "cost",
            "quote",
            "buy",
            "purchase",
            "book",
            "booking",
            "urgent",
            "today",
            "interested",
            "demo",
            "call",
        ]

        for signal in buying_signals:
            if signal in requirement:
                score += 5

        score = min(score, 100)

        if score >= 70:
            status = "qualified"
            stage = "qualified"
            probability = 70
        elif score >= 45:
            status = "contacted"
            stage = "contacted"
            probability = 40
        else:
            status = "new"
            stage = "new"
            probability = 10

        analysis = {
            "score": score,
            "classification": status,
            "source": "lead_qualification_engine",
            "generated_at": datetime.utcnow().isoformat(),
        }

        updated = datetime.utcnow().isoformat()

        db.execute(
            """
            UPDATE leads
            SET
                status = ?,
                score = ?,
                ai_analysis = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                score,
                json.dumps(analysis),
                updated,
                lead_id,
            ),
        )

        db.execute(
            """
            UPDATE sales_opportunities
            SET
                stage = ?,
                probability = ?,
                updated_at = ?
            WHERE lead_id = ?
            """,
            (
                stage,
                probability,
                updated,
                lead_id,
            ),
        )

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
                "lead_qualified",
                json.dumps(analysis),
                updated,
            ),
        )

        db.commit()

        return {
            "lead_id": lead_id,
            "status": status,
            "score": score,
            "probability": probability,
            "analysis": analysis,
        }

    finally:
        db.close()
