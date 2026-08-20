import os
import time
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY")

# Use the model available to your Gemini API account.
MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini client initialized.")
    except Exception as error:
        print("Gemini client initialization failed:")
        print(error)
        client = None
else:
    print("GEMINI_API_KEY not found.")
    print("AI Agent Control Tower will use DEMO MODE.")


# ============================================================
# DEMO FALLBACK
# ============================================================

def demo_response(prompt: str) -> str:

    prompt_lower = prompt.lower()

    if "research" in prompt_lower:
        return """
DEMO AI RESEARCH RESULT

The AI Agent Control Tower analyzed the requested business objective.

Key findings:

• AI customer-support automation can reduce repetitive work.
• Lead qualification is a practical automation opportunity.
• Automated follow-up can improve response consistency.
• CRM automation can reduce manual data entry.
• Automated reporting can save administrative time.

Recommended focus:

Start with lead qualification and automated follow-up because
these workflows have clear business outcomes and can be measured.

Confidence:
Demo analysis — not live market research.
"""

    if "analysis" in prompt_lower:
        return """
DEMO AI ANALYSIS

Business Opportunity:
High

Customer Demand:
High

Implementation Difficulty:
Medium

Competition:
Medium to High

Potential ROI:
Potentially High

Recommended approach:

Build a focused automation workflow around one measurable
business problem instead of selling generic AI services.

Priority:

1. Lead qualification
2. Customer follow-up
3. CRM automation
4. Reporting automation
5. Customer support

Recommendation:

Start with one narrow business workflow and measure the
time saved, leads processed and conversion improvement.
"""

    if "report" in prompt_lower:
        return """
DEMO BUSINESS REPORT

AI Agent Control Tower

EXECUTIVE SUMMARY

The recommended strategy is to build a focused AI automation
service that solves a repetitive and measurable business problem.

RECOMMENDED WORKFLOW

Lead
↓
AI qualification
↓
CRM update
↓
Personalized follow-up
↓
Human sales handoff

BUSINESS BENEFITS

• Faster response
• Less manual work
• Better lead organization
• Consistent follow-up
• Easier scaling

NEXT STEP

Pilot the workflow with one real business and measure:

• Time saved
• Leads processed
• Response time
• Conversion rate

Status:
DEMO COMPLETED
"""

    return f"""
DEMO AI RESULT

The AI Agent Control Tower successfully processed the task.

Business objective:

{prompt}

Recommendation:

Convert this objective into a measurable automation workflow
with clear inputs, AI processing steps and a defined business
outcome.

Status:
DEMO COMPLETED
"""


# ============================================================
# AI ENGINE
# ============================================================

def ask_ai(prompt: str, retries: int = 2) -> str:

    # --------------------------------------------------------
    # Validate prompt
    # --------------------------------------------------------

    if not prompt or not str(prompt).strip():
        return "No AI prompt was provided."

    prompt = str(prompt).strip()

    # --------------------------------------------------------
    # No API client
    # --------------------------------------------------------

    if client is None:

        print("AI DEMO MODE")
        print("Gemini API client unavailable.")

        return demo_response(prompt)

    # --------------------------------------------------------
    # Gemini request
    # --------------------------------------------------------

    last_error = None

    for attempt in range(1, retries + 1):

        try:

            print(
                f"Sending request to Gemini "
                f"(attempt {attempt}/{retries})..."
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            # ------------------------------------------------
            # Validate response
            # ------------------------------------------------

            if response is None:
                raise RuntimeError(
                    "Gemini returned no response."
                )

            text = getattr(response, "text", None)

            if text and str(text).strip():

                print("Gemini response received.")

                return str(text).strip()

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        except Exception as error:

            last_error = error
            error_text = str(error)

            print("Gemini error:")
            print(error_text)

            # ------------------------------------------------
            # Quota / rate limit
            # ------------------------------------------------

            quota_error = (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "quota" in error_text.lower()
                or "rate limit" in error_text.lower()
            )

            if quota_error:

                print("")
                print("Gemini quota/rate limit reached.")
                print("Switching to DEMO MODE.")

                return demo_response(prompt)

            # ------------------------------------------------
            # Temporary server error
            # ------------------------------------------------

            temporary_error = (
                "500" in error_text
                or "503" in error_text
                or "UNAVAILABLE" in error_text
                or "INTERNAL" in error_text
                or "timeout" in error_text.lower()
            )

            if temporary_error:

                if attempt < retries:

                    wait_time = attempt * 3

                    print(
                        f"Temporary Gemini error."
                    )

                    print(
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

                print("Gemini remains unavailable.")
                print("Switching to DEMO MODE.")

                return demo_response(prompt)

            # ------------------------------------------------
            # Authentication error
            # ------------------------------------------------

            authentication_error = (
                "401" in error_text
                or "403" in error_text
                or "API key" in error_text.lower()
                or "api_key" in error_text.lower()
                or "permission" in error_text.lower()
                or "authentication" in error_text.lower()
            )

            if authentication_error:

                print("")
                print("Gemini API authentication problem.")
                print("Check GEMINI_API_KEY.")
                print("Switching to DEMO MODE.")

                return demo_response(prompt)

            # ------------------------------------------------
            # Model error
            # ------------------------------------------------

            model_error = (
                "404" in error_text
                or "not found" in error_text.lower()
                or "model" in error_text.lower()
            )

            if model_error:

                print("")
                print("Gemini model error.")
                print(f"Configured model: {MODEL_NAME}")
                print("Switching to DEMO MODE.")

                return demo_response(prompt)

            # ------------------------------------------------
            # Unknown error
            # ------------------------------------------------

            print("")
            print("Unexpected Gemini error.")
            print("Switching to DEMO MODE.")

            return demo_response(prompt)

    # ========================================================
    # FINAL FALLBACK
    # ========================================================

    print("")
    print("Gemini failed after all attempts.")
    print("Last error:")
    print(last_error)
    print("Switching to DEMO MODE.")

    return demo_response(prompt)