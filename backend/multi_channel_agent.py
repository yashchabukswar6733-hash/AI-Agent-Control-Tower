import json

from .leads import lead_manager
from .lead_agent import analyze_lead_with_ai
from .channel_service import send_message


class MultiChannelSalesAgent:

    def process(
        self,
        business_id,
        channel,
        customer_id,
        name,
        email="",
        business="",
        requirement=""
    ):

        # ----------------------------------------------------
        # 1. CREATE CRM LEAD
        # ----------------------------------------------------

        lead = lead_manager.create_lead(
            business_id=business_id,
            name=name,
            phone=customer_id if channel != "email" else "",
            email=email,
            business=business,
            requirement=requirement
        )

        lead_id = lead["id"]

        # ----------------------------------------------------
        # 2. AI QUALIFICATION
        # ----------------------------------------------------

        ai = analyze_lead_with_ai(
            lead
        )

        analysis = json.dumps(
            {
                "temperature": ai.get(
                    "temperature",
                    "COLD"
                ),
                "business_problem": ai.get(
                    "business_problem",
                    ""
                ),
                "recommended_package": ai.get(
                    "recommended_package",
                    "STARTER"
                ),
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

        updated = lead_manager.update_lead(
            business_id=business_id,
            lead_id=lead_id,
            status="qualified",
            score=ai.get(
                "score",
                0
            ),
            ai_analysis=analysis,
            follow_up=ai.get(
                "follow_up",
                ""
            )
        )

        # ----------------------------------------------------
        # 3. GENERATE CUSTOMER RESPONSE
        # ----------------------------------------------------

        reply = ai.get(
            "sales_reply",
            ""
        )

        if not reply:

            reply = (
                "Thanks for contacting us. "
                "We have received your requirement "
                "and will help you with the next steps."
            )

        # ----------------------------------------------------
        # 4. SEND THROUGH CHANNEL
        # ----------------------------------------------------

        delivery = send_message(
            channel=channel,
            recipient=customer_id
            if channel != "email"
            else email,
            message=reply
        )

        return {
            "success": True,
            "lead_id": lead_id,
            "channel": channel,
            "ai_score": ai.get(
                "score",
                0
            ),
            "temperature": ai.get(
                "temperature",
                "COLD"
            ),
            "recommended_package": ai.get(
                "recommended_package",
                "STARTER"
            ),
            "reply": reply,
            "delivery": delivery,
            "lead": updated
        }


sales_agent = MultiChannelSalesAgent()
