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
You are an AI sales qualification agent for AutoPilot AI.

AutoPilot AI sells business automation services.

STARTER:
Rs 4,999 one-time
1 automation workflow
Basic AI lead handling
Basic integration

GROWTH:
Rs 14,999 one-time
Multiple AI workflows
Lead automation
WhatsApp integration
Ongoing optimization

Analyze this business lead.

Name: {lead.get("name", "")}
Phone: {lead.get("phone", "")}
Email: {lead.get("email", "")}
Business: {lead.get("business", "")}
Requirement: {lead.get("requirement", "")}

Return ONLY valid JSON:

{{
    "score": 0,
    "temperature": "HOT",
    "business_problem": "",
    "recommended_package": "STARTER",
    "reason": "",
    "sales_reply": "",
    "next_action": "",
    "follow_up": ""
}}

Rules:

score must be 0-100.

HOT = clear problem and strong buying potential.
WARM = real problem but uncertain buying intent.
COLD = unclear requirement or weak buying intent.

recommended_package must be STARTER or GROWTH.

sales_reply must be a short professional WhatsApp-style reply.

Do not claim that work has already been completed.

Do not make false promises.

Do not pressure the customer.

next_action must tell the salesperson what to do next.

follow_up must contain a practical follow-up instruction.

Keep the response concise.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    raw = response.text

    data = json.loads(
        clean_json(raw)
    )

    return normalize_ai_result(data)


def analyze_lead_with_ai(lead):

    # =====================================================
    # 1. PRIMARY AI — GEMINI
    # =====================================================

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

    # =====================================================
    # 2. BACKUP AI — OPENROUTER FREE
    # =====================================================

    try:

        print(
            "AI Agent: Gemini unavailable."
        )

        print(
            "AI Agent: Trying OpenRouter backup..."
        )

        result = analyze_with_openrouter(lead)

        result = normalize_ai_result(result)

        print(
            "AI Agent: OpenRouter succeeded."
        )

        return result

    except Exception as openrouter_error:

        print(
            "AI Agent: OpenRouter failed:",
            str(openrouter_error)
        )

    # =====================================================
    # 3. FINAL FALLBACK — LOCAL AGENT
    # =====================================================

    print(
        "AI Agent: Both AI providers unavailable."
    )

    print(
        "AI Agent: Using local fallback."
    )

    result = fallback_analysis(lead)

    result = normalize_ai_result(result)

    return result


def process_lead(lead_id):

    lead = lead_manager.get_lead(
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
