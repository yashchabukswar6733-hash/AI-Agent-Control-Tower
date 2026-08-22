import json

from .database import get_db, new_id, now
from .lead_agent import analyze_lead_with_ai
from .leads import lead_manager
from .proposals import create_proposal


class SalesAgent:

    def process_lead(self, business_id, lead_id):

        lead = lead_manager.get_lead(
            business_id,
            lead_id
        )

        if not lead:
            raise ValueError("Lead not found")

        # --------------------------------------------------
        # AI SALES QUALIFICATION
        # --------------------------------------------------

        ai = analyze_lead_with_ai(lead)

        score = int(ai.get("score", 0))
        temperature = ai.get("temperature", "COLD")
        package = ai.get(
            "recommended_package",
            "STARTER"
        )

        # --------------------------------------------------
        # SAVE AI QUALIFICATION
        # --------------------------------------------------

        analysis = json.dumps(
            {
                "temperature": temperature,
                "business_problem": ai.get(
                    "business_problem",
                    ""
                ),
                "recommended_package": package,
                "reason": ai.get(
                    "reason",
                    ""
                ),
                "sales_reply": ai.get(
                    "sales_reply",
                    ""
                ),
                "next_action": ai.get(
                    "next_action",
                    ""
                )
            },
            ensure_ascii=False
        )

        lead_manager.update_lead(
            business_id=business_id,
            lead_id=lead_id,
            status="qualified",
            score=score,
            ai_analysis=analysis,
            follow_up=ai.get(
                "follow_up",
                ""
            )
        )

        # --------------------------------------------------
        # SALES DECISION
        # --------------------------------------------------

        if temperature == "HOT":

            stage = "qualified"

        elif temperature == "WARM":

            stage = "contacted"

        else:

            stage = "nurture"

        # --------------------------------------------------
        # CREATE PROPOSAL FOR BUYING-READY LEADS
        # --------------------------------------------------

        proposal = None

        if temperature in ["HOT", "WARM"]:

            if package == "GROWTH":

                setup_fee = 14999
                monthly_fee = 0

            else:

                setup_fee = 4999
                monthly_fee = 0

            proposal = create_proposal(
                lead_id=lead_id,
                client_name=lead.get(
                    "name",
                    ""
                ),
                company=lead.get(
                    "business",
                    ""
                ),
                service="AI Business Automation",
                setup_fee=setup_fee,
                monthly_fee=monthly_fee,
                description=(
                    "AI-powered lead handling, "
                    "sales qualification, "
                    "follow-ups and business "
                    "automation."
                ),
                business_id=business_id
            )

        # --------------------------------------------------
        # SALES ACTIVITY
        # --------------------------------------------------

        with get_db() as db:

            db.execute(
                """
                INSERT INTO activity_log
                (
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
                    "sales_agent_processed",
                    json.dumps(
                        {
                            "score": score,
                            "temperature": temperature,
                            "package": package,
                            "stage": stage
                        },
                        ensure_ascii=False
                    ),
                    now()
                )
            )

        return {
            "success": True,
            "lead_id": lead_id,
            "score": score,
            "temperature": temperature,
            "package": package,
            "stage": stage,
            "sales_reply": ai.get(
                "sales_reply",
                ""
            ),
            "next_action": ai.get(
                "next_action",
                ""
            ),
            "follow_up": ai.get(
                "follow_up",
                ""
            ),
            "proposal": proposal
        }


sales_agent = SalesAgent()
