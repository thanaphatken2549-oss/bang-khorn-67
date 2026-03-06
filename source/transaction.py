import secrets
from datetime import datetime
from person import Customer, Member


# ==========================================
# --- Order Hierarchy ---
# ==========================================

class Order:
    def __init__(self, customer: Customer, order_type: str):
        self._order_id = f"ORD-{secrets.token_hex(3).upper()}"
        self._customer = customer
        self._basket = customer.get_basket()
        self._order_type = order_type
        self._status = "Pending"
        self._total_price = 0.0
        self._payment = None
        self._is_paid = False

    def get_order_id(self) -> str: return self._order_id
    def get_customer(self) -> Customer: return self._customer
    def update_status(self, status: str): self._status = status

    def get_payment(self): return self._payment
    def set_payment(self, payment): self._payment = payment

    def set_paid_status(self, status: bool): self._is_paid = status
    def check_payment_status(self) -> bool: return self._is_paid

    def calculate_total(self) -> float:
        sub_total = 0
        for item in self._basket.get_basket_items():
            sub_total += (item.get_product_order_item().get_price() * item.get_qty())

        discount = 0.0
        if isinstance(self._customer, Member):
            discount_rate = self._customer.get_tier().get_discount_rate()
            discount = sub_total * discount_rate

        self._total_price = sub_total - discount
        return self._total_price

    def calculate_member_point(self) -> int:
        return int(self._total_price // 10)

    def process_refund(self):
        if self._payment:
            amount = self._payment.get_payment_amount()
            self._payment.refund(self._customer, amount)
            self._payment.update_status("Voided(Refunded)")
        return True


class OnsiteOrder(Order):
    def __init__(self, customer: Customer, order_type: str):
        super().__init__(customer, order_type)


class OnlineOrder(Order):
    def __init__(self, customer: Customer, order_type: str, delivery_address: str, distance_km: float, payment_window: datetime):
        super().__init__(customer, order_type)
        self.__delivery_address = delivery_address
        self.__delivery_distance_km = distance_km
        self.__payment_window = payment_window
        self.__assigned_rider = None
        self.__delivery_fee = 0.0

    def calculate_total(self, vehicle=None) -> float:
        base_total = super().calculate_total()
        if vehicle:
            self.__delivery_fee = vehicle.calculate_delivery_fee(self.__delivery_distance_km)
            if isinstance(self._customer, Member):
                free_km = self._customer.get_tier().get_free_delivery_km()
                if self.__delivery_distance_km <= free_km:
                    self.__delivery_fee = 0.0
        self._total_price = base_total + self.__delivery_fee
        return self._total_price

    def assign_rider(self, rider):
        self.__assigned_rider = rider

    def get_delivery_fee(self) -> float:
        return self.__delivery_fee


# --- Payment ---
class PaymentChannel:
    def __init__(self, channel_type: str):
        self._channel_type = channel_type

    def get_channel_type(self) -> str:
        return self._channel_type


class QRPayment(PaymentChannel):
    def __init__(self):
        super().__init__("QR")

    def generate_qr_code(self, amount: float) -> str:
        return f"QR_IMG_DATA_FOR_{amount}_THB"


class CashPayment(PaymentChannel):
    def __init__(self, received_amount: float):
        super().__init__("CASH")
        self.__received_amount = received_amount

    def calculate_change(self, total_amount: float) -> float:
        if self.__received_amount < total_amount:
            raise ValueError("จำนวนเงินไม่เพียงพอ")
        return self.__received_amount - total_amount


class Payment:
    def __init__(self, order: OnsiteOrder, payment_channel: PaymentChannel, amount: float):
        self.__order = order
        self.__payment_channel = payment_channel
        self.__amount = amount
        self.__status = "Pending"
        self.__timestamps = datetime.now()

    def set_status(self, status: str):
        self.__status = status
        if status == "Success":
            self.__order.set_paid_status(True)

    def get_status(self) -> str:
        return self.__status
