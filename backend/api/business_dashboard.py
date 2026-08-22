from fastapi import APIRouter

from backend.database import get_db

router = APIRouter(
    prefix="/business-dashboard",
    tags=["Business Dashboard"]
)


@router.get("")
def business_dashboard():

    with get_db() as db:

        clients = db.execute(
            "SELECT COUNT(*) AS total FROM clients"
        ).fetchone()["total"]

        leads = db.execute(
            "SELECT COUNT(*) AS total FROM leads"
        ).fetchone()["total"]

        new_leads = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM leads
            WHERE status = 'new'
            """
        ).fetchone()["total"]

        contacted_leads = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM leads
            WHERE status = 'contacted'
            """
        ).fetchone()["total"]

        won_leads = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM leads
            WHERE status = 'won'
            """
        ).fetchone()["total"]

        conversations = db.execute(
            """
            SELECT COUNT(DISTINCT customer_phone) AS total
            FROM whatsapp_messages
            """
        ).fetchone()["total"]

        inbound_messages = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM whatsapp_messages
            WHERE direction = 'inbound'
            """
        ).fetchone()["total"]

        outbound_messages = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM whatsapp_messages
            WHERE direction = 'outbound'
            """
        ).fetchone()["total"]

        sales = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM sales_opportunities
            """
        ).fetchone()["total"]

        won_sales = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM sales_opportunities
            WHERE stage = 'won'
            """
        ).fetchone()["total"]

        payments = db.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'paid'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS collected,

                COALESCE(
                    SUM(
                        CASE
                            WHEN status = 'pending'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS pending
            FROM payments
            """
        ).fetchone()

    return {
        "clients": clients,
        "leads": {
            "total": leads,
            "new": new_leads,
            "contacted": contacted_leads,
            "won": won_leads
        },
        "whatsapp": {
            "conversations": conversations,
            "inbound_messages": inbound_messages,
            "outbound_messages": outbound_messages
        },
        "sales": {
            "total": sales,
            "won": won_sales
        },
        "revenue": {
            "collected": float(payments["collected"] or 0),
            "pending": float(payments["pending"] or 0)
        }
    }
