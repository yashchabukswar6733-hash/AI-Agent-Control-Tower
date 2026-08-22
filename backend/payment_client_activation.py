from .client_activation import activate_paid_client


def activate_client_from_verified_payment(
    payment,
    razorpay_payment_id
):
    """
    Called ONLY after the Razorpay webhook signature
    and payment event have already been verified.

    This function never trusts browser/frontend payment data.
    """

    if not payment:
        raise ValueError("Internal payment record is required.")

    business_id = payment["business_id"]

    if not business_id:
        raise ValueError(
            "Payment does not belong to a business."
        )

    result = activate_paid_client(
        business_id=business_id,
        client_name=payment["client_name"],
        company=payment["company"],
        phone="",
        email="",
        payment_id=payment["id"]
    )

    return {
        "success": True,
        "payment_id": payment["id"],
        "razorpay_payment_id": razorpay_payment_id,
        "business_id": business_id,
        "client_id": result["client_id"],
        "onboarding_id": result["onboarding_id"],
        "status": result["status"]
    }
