const API_BASE = window.LEADPILOT_API_BASE || "http://127.0.0.1:8000";

function getPublicBusinessKey() {
    const params = new URLSearchParams(window.location.search);

    return (
        params.get("public_key") ||
        window.LEADPILOT_PUBLIC_KEY ||
        ""
    ).trim();
}

async function submitLead(form) {
    const submitButton = form.querySelector(
        'button[type="submit"], input[type="submit"]'
    );

    const originalText = submitButton
        ? submitButton.textContent
        : "";

    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Sending...";
    }

    const data = new FormData(form);

    const payload = {
        public_key: getPublicBusinessKey(),
        name: String(data.get("name") || "").trim(),
        phone: String(data.get("phone") || "").trim(),
        email: String(data.get("email") || "").trim(),
        business: String(data.get("business") || "").trim(),
        requirement: String(data.get("requirement") || "").trim(),
        source: "customer_website"
    };

    if (!payload.public_key) {
        throw new Error(
            "This customer website is not connected to a business account."
        );
    }

    if (!payload.name) {
        throw new Error("Please enter your name.");
    }

    if (!payload.phone && !payload.email) {
        throw new Error(
            "Please provide a phone number or email address."
        );
    }

    const response = await fetch(
        `${API_BASE}/public/leads`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        }
    );

    let result = {};

    try {
        result = await response.json();
    } catch (_) {
        result = {};
    }

    if (!response.ok) {
        throw new Error(
            result.detail ||
            "Unable to submit your enquiry."
        );
    }

    return result;
}


function installLeadForms() {
    const forms = document.querySelectorAll(
        "form[data-lead-form], #lead-form, .lead-form"
    );

    forms.forEach((form) => {
        if (form.dataset.leadpilotInstalled === "true") {
            return;
        }

        form.dataset.leadpilotInstalled = "true";

        form.addEventListener(
            "submit",
            async (event) => {
                event.preventDefault();

                const status = form.querySelector(
                    "[data-lead-status]"
                );

                try {
                    const result = await submitLead(form);

                    if (status) {
                        status.textContent =
                            result.message ||
                            "Your enquiry has been received successfully.";
                    }

                    form.reset();

                } catch (error) {
                    if (status) {
                        status.textContent =
                            error.message ||
                            "Unable to submit your enquiry.";
                    } else {
                        alert(
                            error.message ||
                            "Unable to submit your enquiry."
                        );
                    }

                } finally {
                    const button = form.querySelector(
                        'button[type="submit"], input[type="submit"]'
                    );

                    if (button) {
                        button.disabled = false;
                        button.textContent =
                            button.dataset.originalText ||
                            "Submit";
                    }
                }
            }
        );
    });
}


if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        installLeadForms
    );
} else {
    installLeadForms();
}
