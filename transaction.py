from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid

app = FastAPI()

# =========================
# Mock Database
# =========================
staff_db = {
    "S001": "Nakhorn",
    "S002": "Pun"
}

order_db = {}

# =========================
# Request Model
# =========================
class CreateTransactionRequest(BaseModel):
    staff_id: str
    order_id: str


# =========================
# Staff
# =========================
class Staff:

    @staticmethod
    def get_staff(staff_id):
        if staff_id not in staff_db:
            raise Exception("Unauthorized Staff")
        return {"id": staff_id, "name": staff_db[staff_id]}


# =========================
# Payment
# =========================
class Payment:
    def __init__(self, amount, status):
        self.amount = amount
        self.status = status

    def check_status(self):
        if self.status != "Success":
            raise Exception("Payment Incomplete")
        return True

    def get_payment_channel(self):
        return self.__class__.__name__


class CashPayment(Payment):
    pass


class QRPayment(Payment):
    pass


# =========================
# Order
# =========================
class Order:

    def __init__(self, order_id, total_amount, payment: Payment):
        self.order_id = order_id
        self.total_amount = total_amount
        self.payment = payment
        order_db[order_id] = self

    @staticmethod
    def get_order_by_id(order_id):
        if order_id not in order_db:
            raise Exception("Order Not Found")
        return order_db[order_id]

    def get_payment(self):
        return self.payment


# =========================
# SaleTransaction
# =========================
class SaleTransaction:

    def __init__(self, staff, order, payment_channel):
        self.transaction_id = str(uuid.uuid4())
        self.staff = staff
        self.order_id = order.order_id
        self.payment_channel = payment_channel
        self.amount = order.total_amount  # ✅ ดึงจาก Order
        self.created_at = datetime.now()

    def generate_receipt(self):
        return {
            "transaction_id": self.transaction_id,
            "staff": self.staff["name"],
            "order_id": self.order_id,
            "payment_channel": self.payment_channel,
            "total_amount": self.amount,   # ✅ แสดงจำนวนเงิน
            "date": str(self.created_at)
        }


# =========================
# ShopController
# =========================
class ShopController:

    @staticmethod
    def create_transaction(staff_id, order_id):

        # 1 Validate Staff
        staff = Staff.get_staff(staff_id)

        # 2 Fetch Order
        order = Order.get_order_by_id(order_id)

        payment = order.get_payment()

        # Check Payment Status
        payment.check_status()

        payment_channel = payment.get_payment_channel()

        # 3 Create Transaction (มี amount แล้ว)
        transaction = SaleTransaction(staff, order, payment_channel)
        receipt = transaction.generate_receipt()

        return receipt


# =========================
# API Endpoint
# =========================
@app.post("/create-transaction")
def create_transaction(request: CreateTransactionRequest):
    try:
        receipt = ShopController.create_transaction(
            request.staff_id,
            request.order_id
        )
        return {
            "status": "Success",
            "message": "Transaction Completed",
            "receipt": receipt
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# Sample Data
# =========================
sample_payment = CashPayment(amount=150, status="Success")
Order("O1001", total_amount=150, payment=sample_payment)
