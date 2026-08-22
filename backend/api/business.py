import json
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.business import Business
from backend.api.auth import get_current_business

router = APIRouter(
    prefix="/business",
    tags=["Business"]
)


class BusinessSettingsRequest(BaseModel):
    business_description: str = ""
    services: list[str] = []
    pricing: str = ""
    sales_instructions: str = ""
    human_handoff_message: str = ""


@router.get("/settings")
def get_business_settings(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    row = db.execute(
        """
        SELECT *
        FROM business_settings
        WHERE business_id = ?
        """,
        (business.id,)
    ).fetchone()

    if not row:
        return {
            "business_id": business.id,
            "business_description": "",
            "services": [],
            "pricing": "",
            "sales_instructions": "",
            "human_handoff_message": ""
        }

    return {
        "business_id": business.id,
        "business_description": row["business_description"],
        "services": json.loads(row["services"] or "[]"),
        "pricing": row["pricing"],
        "sales_instructions": row["sales_instructions"],
        "human_handoff_message": row["human_handoff_message"]
    }


@router.put("/settings")
def update_business_settings(
    data: BusinessSettingsRequest,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    updated_at = datetime.utcnow().isoformat()

    existing = db.execute(
        """
        SELECT id
        FROM business_settings
        WHERE business_id = ?
        """,
        (business.id,)
    ).fetchone()

    values = (
        data.business_description.strip(),
        json.dumps(data.services),
        data.pricing.strip(),
        data.sales_instructions.strip(),
        data.human_handoff_message.strip(),
        updated_at
    )

    if existing:
        db.execute(
            """
            UPDATE business_settings
            SET business_description = ?,
                services = ?,
                pricing = ?,
                sales_instructions = ?,
                human_handoff_message = ?,
                updated_at = ?
            WHERE business_id = ?
            """,
            values + (business.id,)
        )
    else:
        db.execute(
            """
            INSERT INTO business_settings
            (
                business_id,
                business_description,
                services,
                pricing,
                sales_instructions,
                human_handoff_message,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (business.id,) + values
        )

    return {
        "message": "Business AI settings saved.",
        "business_id": business.id
    }


@router.put("/whatsapp")
def connect_whatsapp(
    phone_number_id: str,
    whatsapp_business_account_id: str,
    access_token: str,
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    db.execute(
        """
        UPDATE businesses
        SET whatsapp_phone_number_id = ?,
            whatsapp_business_account_id = ?,
            whatsapp_access_token = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            phone_number_id.strip(),
            whatsapp_business_account_id.strip(),
            access_token.strip(),
            datetime.utcnow().isoformat(),
            business.id
        )
    )

    return {
        "message": "WhatsApp configuration saved.",
        "business_id": business.id,
        "phone_number_id": phone_number_id
    }
