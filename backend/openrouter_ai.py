import os
import json
import requests


def analyze_with_openrouter(lead):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    prompt = f"""
You are a professional sales qualification AI for an automation agency.

Analyze this lead:

Name: {lead.get("name", "")}
Phone: {lead.get("phone", "")}
Email: {lead.get("email", "")}
Business: {lead.get("business", "")}
Requirement: {lead.get("requirement", "")}

Return ONLY valid JSON:

{{
  "temperature": "HOT|WARM|COLD",
  "score": 0,
  "business_problem": "",
  "recommended_package": "STARTER|GROWTH|PRO",
  "reason": "",
  "sales_reply": "",
  "next_action": ""
}}

Scoring:
0-39 = COLD
40-69 = WARM
70-100 = HOT

Never claim the customer purchased anything.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:8000",
            "X-Title": "AutoPilot AI Lead Agent"
        },
        json={
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        },
        timeout=45
    )

    response.raise_for_status()

    data = response.json()

    content = data["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    return json.loads(content)


def fallback_analysis(lead):
    requirement = str(lead.get("requirement", "")).lower()
    business = str(lead.get("business", "")).strip()

    automation_words = [
        "whatsapp",
        "automation",
        "enquiry",
        "enquiries",
        "lead",
        "chat",
        "customer",
        "follow up"
    ]

    if any(word in requirement for word in automation_words):

        return {
            "temperature": "WARM",
            "score": 65,
            "business_problem": "The business appears to need automated lead handling and customer communication.",
            "recommended_package": "GROWTH",
            "reason": "The enquiry indicates an automation requirement that matches the Growth package.",
            "sales_reply": (
                f"Hi! Thanks for contacting AutoPilot AI. "
                f"We can help {business or 'your business'} automate lead handling "
                f"and customer communication. Would you be available for a quick "
                f"5-minute discussion?"
            ),
            "next_action": "Contact the lead and verify the requirement before preparing a proposal."
        }

    return {
        "temperature": "COLD",
        "score": 30,
        "business_problem": "The enquiry does not contain enough information to identify a strong automation opportunity.",
        "recommended_package": "STARTER",
        "reason": "More information is required before recommending an automation package.",
        "sales_reply": (
            "Hi! Thanks for contacting AutoPilot AI. "
            "Could you tell us a little more about the process you want to automate?"
        ),
        "next_action": "Ask qualification questions and determine the business problem."
    }
