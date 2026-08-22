import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parent / "saas.db"


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return uuid.uuid4().hex


def save_incoming_message(
    business_id,
    customer_phone,
    message_text,
    provider_message_id="",
    customer_name=""
):
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    conversation = db.execute(
        """
        SELECT *
        FROM whatsapp_conversations
        WHERE business_id = ?
          AND customer_phone = ?
          AND status = 'open'
        LIMIT 1
        """,
        (business_id, customer_phone)
    ).fetchone()

    if conversation:
        conversation_id = conversation["id"]
    else:
        conversation_id = new_id()

        db.execute(
            """
            INSERT INTO whatsapp_conversations
            (
                id,
                business_id,
                customer_phone,
                customer_name,
                status,
                last_message_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 'open', ?, ?, ?)
            """,
            (
                conversation_id,
                business_id,
                customer_phone,
                customer_name,
                now(),
                now(),
                now()
            )
        )

    message_id = new_id()

    db.execute(
        """
        INSERT INTO whatsapp_messages
        (
            id,
            business_id,
            conversation_id,
            customer_phone,
            direction,
            message_text,
            provider_message_id,
            ai_generated,
            delivery_status,
            created_at
        )
        VALUES (?, ?, ?, ?, 'incoming', ?, ?, 0, 'received', ?)
        """,
        (
            message_id,
            business_id,
            conversation_id,
            customer_phone,
            message_text,
            provider_message_id,
            now()
        )
    )

    db.execute(
        """
        UPDATE whatsapp_conversations
        SET last_message_at = ?,
            updated_at = ?
        WHERE id = ?
          AND business_id = ?
        """,
        (
            now(),
            now(),
            conversation_id,
            business_id
        )
    )

    db.commit()
    db.close()

    return {
        "conversation_id": conversation_id,
        "message_id": message_id,
        "business_id": business_id,
        "customer_phone": customer_phone
    }


def save_outgoing_message(
    business_id,
    conversation_id,
    customer_phone,
    message_text,
    provider_message_id="",
    ai_generated=False,
    delivery_status="sent"
):
    db = sqlite3.connect(DB)

    message_id = new_id()

    db.execute(
        """
        INSERT INTO whatsapp_messages
        (
            id,
            business_id,
            conversation_id,
            customer_phone,
            direction,
            message_text,
            provider_message_id,
            ai_generated,
            delivery_status,
            created_at
        )
        VALUES (?, ?, ?, ?, 'outgoing', ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            business_id,
            conversation_id,
            customer_phone,
            message_text,
            provider_message_id,
            1 if ai_generated else 0,
            delivery_status,
            now()
        )
    )

    db.execute(
        """
        UPDATE whatsapp_conversations
        SET last_message_at = ?,
            updated_at = ?
        WHERE id = ?
          AND business_id = ?
        """,
        (
            now(),
            now(),
            conversation_id,
            business_id
        )
    )

    db.commit()
    db.close()

    return message_id
