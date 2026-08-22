import os
import json
import re
import requests

from .leads import lead_manager
from .lead_agent import process_lead


# ============================================================
# OPENROUTER CONFIG
# ============================================================

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/free"


# ============================================================
# BUSINESS CONFIG
# ============================================================

SYSTEM_PROMPT = """
You are the customer-facing AI sales assistant for AutoPilot AI.

AutoPilot AI helps businesses automate repetitive work.

PACKAGES:

STARTER - ?4,999 one-time
- 1 automation workflow
- Basic AI lead handling
- Basic integration

GROWTH - ?14,999 one-time
- Multiple AI workflows
- Lead automation
- WhatsApp automation
- Workflow optimization

Your job:
1. Understand what the customer needs.
2. Explain suitable automation.
3. Recommend STARTER or GROWTH.
4. Detect buying interest.
5. Ask for contact information when appropriate.
6. Never claim that an automation is already installed.
7. Never guarantee revenue or results.
8. Never ask for passwords, OTPs, bank details or sensitive information.
9. Never pretend a human has already contacted the customer.

Qualification:
- cold = general information
- warm = clear business problem or automation interest
- hot = strong buying interest
- qualified = complete contact information and buying/contact intent

IMPORTANT:
Return ONLY valid JSON.

JSON format:

{
  "reply": "customer-facing response",
  "intent": "information|interested|buying|contact",
  "recommended_package": "STARTER|GROWTH|NONE",
  "collect_contact": true,
  "next_question": "next useful question",
  "qualification": "cold|warm|hot|qualified",
  "business": "business name or empty",
  "requirement": "customer requirement"
}
"""


# ============================================================
# OPENROUTER CALL
# ============================================================

def call_openrouter(prompt):

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 700
    }

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "AutoPilot AI Customer Agent"
        },
        json=payload,
        timeout=45
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )

    result = response.json()

    try:
        return result["choices"][0]["message"]["content"].strip()
    except Exception:
        raise RuntimeError(
            f"Unexpected OpenRouter response: {result}"
        )


# ============================================================
# CONTACT EXTRACTION
# ============================================================

def extract_contact(text):

    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    phone_match = re.search(
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
        text
    )

    email = (
        email_match.group(0)
        if email_match
        else ""
    )

    phone = (
        phone_match.group(0)
        if phone_match
        else ""
    )

    name = ""
    business = ""

    name_patterns = [
        r"(?:my name is|i am|i'm|this is)\s+([A-Za-z][A-Za-z .'-]{1,40})",
        r"(?:name)\s*[:=-]\s*([A-Za-z][A-Za-z .'-]{1,40})"
    ]

    for pattern in name_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            name = match.group(1).strip()

            # Stop accidental capture of following phrases.
            name = re.split(
                r"\s+(?:and|my|i|phone|email|from)\s+",
                name,
                flags=re.IGNORECASE
            )[0].strip()

            break

    business_patterns = [
        r"(?:business|company|clinic|shop|restaurant)\s*(?:name)?\s*[:=-]\s*([A-Za-z0-9 &.'-]{2,80})",
        r"(?:i run|i own|owner of)\s+([A-Za-z0-9 &.'-]{2,80})"
    ]

    for pattern in business_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            business = match.group(1).strip()

            business = re.split(
                r"\s+(?:my|phone|email|and)\s+",
                business,
                flags=re.IGNORECASE
            )[0].strip()

            break

    return {
        "name": name,
        "phone": phone,
        "email": email,
        "business": business
    }


# ============================================================
# JSON CLEANER
# ============================================================

def parse_ai_response(raw):

    if not raw:
        return None

    raw = str(raw).strip()

    # Remove model thinking blocks if present
    raw = re.sub(
        r"<think>.*?</think>",
        "",
        raw,
        flags=re.DOTALL | re.IGNORECASE
    ).strip()

    # Remove markdown JSON fences
    raw = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw
    ).strip()

    # First attempt: complete response is JSON
    try:
        data = json.loads(raw)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    # Second attempt: find the JSON object
    start_json = raw.find("{")
    end_json = raw.rfind("}")

    if start_json >= 0 and end_json > start_json:

        candidate = raw[start_json:end_json + 1]

        try:
            data = json.loads(candidate)

            if isinstance(data, dict):
                return data

        except Exception:
            pass

    return None

# ============================================================
# LOCAL FALLBACK
# ============================================================

def fallback_response(message, contact):

    text = message.lower()

    if any(
        word in text
        for word in [
            "whatsapp",
            "automation",
            "lead",
            "appointment",
            "follow up",
            "follow-up"
        ]
    ):

        return {
            "reply": (
                "Yes, we can help automate that. "
                "For WhatsApp, lead handling and "
                "follow-ups, the GROWTH package at "
                "?14,999 one-time is usually the better fit. "
                "Would you like to tell me more about your business?"
            ),
            "intent": "interested",
            "recommended_package": "GROWTH",
            "collect_contact": True,
            "next_question": (
                "What type of business do you run, "
                "and what would you like to automate?"
            ),
            "qualification": "warm",
            "business": contact["business"],
            "requirement": message
        }

    return {
        "reply": (
            "I'd be happy to help. Tell me which "
            "business process you want to automate."
        ),
        "intent": "information",
        "recommended_package": "NONE",
        "collect_contact": False,
        "next_question": (
            "What process is currently taking "
            "the most time?"
        ),
        "qualification": "cold",
        "business": contact["business"],
        "requirement": message
    }


# ============================================================
# MAIN CUSTOMER AGENT
# ============================================================

def customer_chat(message, conversation=None):

    if not message or not message.strip():

        return {
            "reply": (
                "Hi! Tell me what you'd like "
                "to automate in your business."
            ),
            "intent": "information",
            "recommended_package": "NONE",
            "collect_contact": False,
            "next_question": (
                "What process is currently "
                "taking the most time?"
            ),
            "contact": {
                "name": "",
                "phone": "",
                "email": "",
                "business": ""
            },
            "lead_created": False,
            "lead_id": None,
            "qualification": "cold",
            "agent": "customer_orchestrator"
        }

    conversation = conversation or []

    history_parts = []

    for item in conversation[-10:]:

        role = item.get(
            "role",
            "user"
        )

        content = item.get(
            "content",
            ""
        )

        history_parts.append(
            f"{role}: {content}"
        )

    history = "\n".join(history_parts)

    full_text = (
        history +
        "\nuser: " +
        message
    )

    contact = extract_contact(
        full_text
    )

    prompt = f"""
Previous conversation:

{history}

Latest customer message:

{message}

Analyze the latest customer message.

Return ONLY JSON.
"""

    # ========================================================
    # AI
    # ========================================================

    try:

        raw = call_openrouter(
            prompt
        )

        data = parse_ai_response(
            raw
        )

        if not data:

            data = fallback_response(
                message,
                contact
            )

            agent_name = "fallback"

        else:

            agent_name = "customer_orchestrator"

    except Exception as e:

        print(
            "OpenRouter warning:",
            str(e)
        )

        data = fallback_response(
            message,
            contact
        )

        agent_name = "fallback"

    # ========================================================
    # NORMALIZE
    # ========================================================

    intent = str(
        data.get(
            "intent",
            "information"
        )
    ).lower()

    if intent not in [
        "information",
        "interested",
        "buying",
        "contact"
    ]:

        intent = "information"

    package = str(
        data.get(
            "recommended_package",
            "NONE"
        )
    ).upper()

    if package not in [
        "STARTER",
        "GROWTH",
        "NONE"
    ]:

        package = "NONE"

    collect_contact = bool(
        data.get(
            "collect_contact",
            False
        )
    )

    qualification = str(
        data.get(
            "qualification",
            "cold"
        )
    ).lower()

    if qualification not in [
        "cold",
        "warm",
        "hot",
        "qualified"
    ]:

        qualification = "cold"

    # ========================================================
    # IMPROVE CONTACT DATA FROM AI
    # ========================================================

    ai_business = str(
        data.get(
            "business",
            ""
        )
    ).strip()

    ai_requirement = str(
        data.get(
            "requirement",
            message
        )
    ).strip()

    if ai_business and not contact["business"]:
        contact["business"] = ai_business

    # ========================================================
    # QUALIFICATION LOGIC
    # ========================================================

    has_contact = bool(
        contact["name"]
        and contact["phone"]
        and contact["email"]
    )

    if has_contact:

        if intent in [
            "buying",
            "contact"
        ]:

            qualification = "qualified"

        elif qualification == "cold":

            qualification = "warm"

    elif intent == "buying":

        qualification = "hot"

    elif (
        intent == "interested"
        and qualification == "cold"
    ):

        qualification = "warm"

    # ========================================================
    # CREATE LEAD
    # ========================================================

    lead_created = False
    lead_id = None

    if has_contact and (
        intent in [
            "buying",
            "contact"
        ]
        or qualification == "qualified"
    ):

        try:

            lead = lead_manager.create_lead(
                name=contact["name"],
                phone=contact["phone"],
                email=contact["email"],
                business=(
                    contact["business"]
                    or "Unknown"
                ),
                requirement=ai_requirement
            )

            if isinstance(
                lead,
                dict
            ):

                lead_id = (
                    lead.get("id")
                    or lead.get("lead_id")
                )

            else:

                lead_id = str(
                    lead
                )

            lead_created = True

            # Automatically send the new lead to the Lead Agent
            if lead_id:
                try:
                    process_lead(lead_id)
                    print(
                        f"Lead Agent: Lead {lead_id} automatically qualified."
                    )
                except Exception as agent_error:
                    print(
                        "Lead Agent warning:",
                        str(agent_error)
                    )

        except Exception as e:

            print(
                "Lead creation warning:",
                str(e)
            )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "reply": str(
            data.get(
                "reply",
                "How can we help?"
            )
        ),

        "intent": intent,

        "recommended_package": package,

        "collect_contact": collect_contact,

        "next_question": str(
            data.get(
                "next_question",
                ""
            )
        ),

        "contact": contact,

        "lead_created": lead_created,

        "lead_id": lead_id,

        "qualification": qualification,

        "agent": agent_name
    }



