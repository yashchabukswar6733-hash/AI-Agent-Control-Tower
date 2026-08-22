from .openrouter_ai import analyze_with_openrouter
from .whatsapp_memory import get_recent_conversation


def generate_customer_reply(
    business_id,
    customer_name,
    customer_phone,
    customer_message,
    business_name="AI Sales"
):

    history = get_recent_conversation(
        business_id,
        customer_phone,
        limit=20
    )

    conversation = ""

    for item in history:

        speaker = (
            "Customer"
            if item["direction"] == "incoming"
            else "AI Sales"
        )

        conversation += (
            f"{speaker}: "
            f"{item['message']}\n"
        )

    prompt = f"""
You are the WhatsApp AI sales assistant for {business_name}.

Customer name: {customer_name}

Previous conversation:
{conversation}

New customer message:
{customer_message}

Reply professionally and naturally.

Rules:
- Answer the customer's actual question.
- Use previous conversation when relevant.
- Do not invent prices, features or guarantees.
- Do not claim a human contacted the customer unless that happened.
- Keep the WhatsApp reply concise.
- If the customer shows buying intent, guide them toward the next sales step.
- Never pressure the customer.

Return JSON only:

{{
    "reply": "",
    "intent": "enquiry",
    "sales_ready": false
}}
"""

    try:

        result = analyze_with_openrouter(
            {
                "name": customer_name,
                "phone": customer_phone,
                "business": business_name,
                "requirement": prompt
            }
        )

        reply = result.get(
            "sales_reply",
            ""
        )

        if reply:
            return reply.strip()

    except Exception as error:

        print(
            "WhatsApp conversation AI error:",
            error
        )

    return (
        f"Hi {customer_name}, thanks for contacting "
        f"{business_name}. Could you tell me a little "
        "more about what you need help with?"
    )


def process_incoming_message(
    business_id,
    customer_name,
    customer_phone,
    message,
    business_name="AI Sales"
):

    return generate_customer_reply(
        business_id=business_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_message=message,
        business_name=business_name
    )
