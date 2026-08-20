from .leads import lead_manager
from .ai_service import ask_ai


def process_lead(lead_id: str):

    lead = lead_manager.get_lead(lead_id)

    if not lead:
        return {
            "error": "Lead not found"
        }

    prompt = f"""
You are an AI sales qualification agent.

Analyze this business lead.

Lead name: {lead['name']}
Business: {lead['business']}
Requirement: {lead['requirement']}

Return exactly this format:

SCORE: [0-100]

CLASSIFICATION: [HOT/WARM/COLD]

REASON:
[2-4 concise sentences explaining the qualification]

FOLLOW_UP:
[Write a professional response to the lead. Do not claim a human has approved or contacted them.]

NEXT_ACTION:
[One practical next step for the business owner]
"""

    result = ask_ai(prompt)

    score = 50

    text = result.upper()

    if "HOT" in text:
        score = 85
    elif "WARM" in text:
        score = 65
    elif "COLD" in text:
        score = 30

    lead_manager.update_lead(
        lead_id,
        score=score,
        ai_analysis=result,
        follow_up=result,
        status="qualified"
    )

    return {
        "message": "Lead processed successfully",
        "lead": lead_manager.get_lead(lead_id)
    }