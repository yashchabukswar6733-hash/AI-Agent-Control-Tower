
from datetime import datetime
import uuid


class PaymentManager:

    def __init__(self):
        self.payments = {}

    def create_payment(
        self,
        proposal_id,
        client_name,
        company,
        amount,
        payment_type="setup",
        description=""
    ):
        payment_id = uuid.uuid4().hex[:8]

        payment = {
            "id": payment_id,
            "proposal_id": proposal_id,
            "client_name": client_name,
            "company": company,
            "amount": float(amount),
            "payment_type": payment_type,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "paid_at": None
        }

        self.payments[payment_id] = payment

        return payment

    def get_payment(self, payment_id):
        return self.payments.get(payment_id)

    def list_payments(self):
        return list(self.payments.values())

    def mark_paid(self, payment_id):
        payment = self.payments.get(payment_id)

        if not payment:
            return None

        payment["status"] = "paid"
        payment["paid_at"] = datetime.now().isoformat()

        return payment

    def cancel_payment(self, payment_id):
        payment = self.payments.get(payment_id)

        if not payment:
            return None

        payment["status"] = "cancelled"

        return payment


payment_manager = PaymentManager()

