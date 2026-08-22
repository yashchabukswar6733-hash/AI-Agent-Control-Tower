import json
import os
import re

from .leads import lead_manager
from .openrouter_ai import analyze_with_openrouter, fallback_analysis


def get_gemini_client():

    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


def clean_json(text):

    text = str(text).strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def normalize_ai_result(data):

    score = int(data.get("score", 0))
    score = max(0, min(100, score))

    temperature = str(
        data.get("temperature", "COLD")
    ).upper()

    if temperature not in ["HOT", "WARM", "COLD"]:

        if score >= 70:
            temperature = "HOT"
        elif score >= 40:
            temperature = "WARM"
        else:
            temperature = "COLD"

    package = str(
        data.get(
            "recommended_package",
            "STARTER"
        )
    ).upper()

    if package not in ["STARTER", "GROWTH"]:
        package = "STARTER"

    data["score"] = score
    data["temperature"] = temperature
    data["recommended_package"] = package

    data.setdefault("business_problem", "")
    data.setdefault("reason", "")
    data.setdefault("sales_reply", "")
    data.setdefault("next_action", "")
    data.setdefault("follow_up", "")

    return data


def analyze_with_gemini(lead):

    client = get_gemini_client()

    if client is None:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    prompt = f"""
You are the AI sales qualification agent for AutoPilot AI.

A customer contacted a business through WhatsApp.

Analyze the customer message and determine the best sales response.

Business:
{lead.get("business", "")}

Customer:
{lead.get("name", "")}

Phone:
{lead.get("phone", "")}

Customer requirement/message:
{lead.get("requirement", "")}

Return ONLY valid JSON:

{{
    "score": 0,
    "temperature": "COLD",
    "business_problem": "",
    "recommended_package": "STARTER",
    "reason": "",
    "sales_reply": "",
    "next_action": "",
    "follow_up": ""
}}

Rules:

score must be 0-100.

HOT = strong buying intent or urgent business problem.
WARM = genuine business problem but uncertain buying intent.
COLD = unclear requirement or weak buying intent.

recommended_package must be STARTER or GROWTH.

sales_reply must be a short professional WhatsApp reply.

The reply must:
- answer the customer naturally
- not claim something has already been completed
- not make false promises
- not pressure the customer
- encourage the customer to explain their requirement
- be concise

Do not mention that you are an AI unless necessary.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    data = json.loads(
        clean_json(response.text)
    )

    return normalize_ai_result(data)


def analyze_lead_with_ai(lead):

    try:

        print("AI Agent: Trying Gemini...")

        result = analyze_with_gemini(lead)

        print("AI Agent: Gemini succeeded.")

        return result

    except Exception as gemini_error:

        print(
            "AI Agent: Gemini failed:",
            str(gemini_error)
        )

    try:

        print(
            "AI Agent: Trying OpenRouter backup..."
        )

        result = analyze_with_openrouter(lead)

        return normalize_ai_result(result)

    except Exception as openrouter_error:

        print(
            "AI Agent: OpenRouter failed:",
            str(openrouter_error)
        )

    print(
        "AI Agent: Using local fallback."
    )

    return normalize_ai_result(
        fallback_analysis(lead)
    )


def process_lead(
    business_id,
    lead_id
):

    lead = lead_manager.get_lead(
        business_id,
        lead_id
    )

    if not lead:
        raise ValueError(
            f"Lead {lead_id} not found"
        )

    print(
        f"AI Agent: Processing lead {lead_id}"
    )

    ai = analyze_lead_with_ai(
        lead
    )

    analysis = json.dumps(
        {
            "temperature": ai["temperature"],
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

    follow_up = ai.get(
        "follow_up",
        ""
    )

    updated = lead_manager.update_lead(
        business_id=business_id,
        lead_id=lead_id,
        status="qualified",
        score=ai["score"],
        ai_analysis=analysis,
        follow_up=follow_up
    )

    return {
        "lead": updated,
        "ai": ai
    }
# ============================================================
# PROCESS LEAD
# ============================================================

def process_lead(
    lead_id,
    business_id
):

    lead = lead_manager.get_lead(
        business_id,
        lead_id
    )

    if not lead:
        raise ValueError(
            f"Lead {lead_id} not found"
        )

    print(
        f"AI Agent: Processing lead {lead_id}"
    )

    ai = analyze_lead_with_ai(
        lead
    )

    analysis = json.dumps(
        {
            "temperature": ai["temperature"],
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

    follow_up = ai.get(
        "follow_up",
        ""
    )

    updated = lead_manager.update_lead(
        business_id=business_id,
        lead_id=lead_id,
        status="qualified",
        score=ai["score"],
        ai_analysis=analysis,
        follow_up=follow_up
    )

    print(
        f"AI Agent: Lead {lead_id} processed successfully."
    )

    return updated
