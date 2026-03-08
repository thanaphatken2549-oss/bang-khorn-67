import secrets, uuid
from datetime import datetime
from person import Customer, Member


# ==========================================
# --- Order Hierarchy ---
# ==========================================

import secrets

class StockSource:
    """จำว่าสินค้าแต่ละตัวถูกหักสต็อกจากที่ไหน (shelf หรือ warehouse)"""
    def __init__(self, product_id: str, source: str):
        self.__product_id = product_id
        self.__source = source

    def get_product_id(self) -> str:
        return self.__product_id

    def get_source(self) -> str:
        return self.__source

    def set_source(self, source: str):
        self.__source = source


class Order:
    def __init__(self, customer, order_type: str):
        # เปลี่ยนเป็น Private (__) ทั้งหมด
        self.__order_id = f"ORD-{secrets.token_hex(3).upper()}"
        self.__customer = customer
        self.__basket = customer.get_basket()
        self.__order_type = order_type
        self.__status = "Pending"
        self.__total_price = 0.0
        self.__payment = None
        self.__assigned_barista = None
        self.__stock_source = []  # 🆕 จำว่าสินค้าแต่ละตัวหักจากไหน

    def get_order_id(self) -> str: return self.__order_id
    def get_customer(self): return self.__customer
    
    # เพิ่ม Getter สำหรับให้คลาสภายนอก หรือ คลาสลูก (OnlineOrder) นำไปใช้
    def get_order_type(self) -> str: return self.__order_type
    def get_total_price(self) -> float: return self.__total_price
    
    # เพิ่ม Setter สำหรับให้ OnlineOrder นำไปอัปเดตยอดรวมบวกค่าส่ง
    def set_total_price(self, price: float): self.__total_price = price

    def update_status(self, status: str): self.__status = status

    def get_payment(self): return self.__payment
    def set_payment(self, payment): self.__payment = payment


    def calculate_total(self) -> float:
        sub_total = 0
        for item in self.__basket.get_basket_items():
            sub_total += (item.get_product_order_item().get_price() * item.get_qty())

        discount = 0.0
        # ต้องมั่นใจว่ามีการ import Member มาแล้ว
        if isinstance(self.__customer, Member):
            discount_rate = self.__customer.get_tier().get_discount_rate()
            discount = sub_total * discount_rate

        self.__total_price = sub_total - discount
        return self.__total_price

    def calculate_member_point(self) -> int:
        return int(self.__total_price // 10)

    def process_refund(self):
        if self.__payment:
            amount = self.__payment.get_amount()
            self.__payment.refund(self.__customer, amount)
            self.__payment.set_status("Voided(Refunded)")
        return True
    # transaction.py — เพิ่มใน class Order (ต่อจาก set_payment)

    def get_basket(self):
        """ดึง basket ที่ผูกกับ order (snapshot ตอนสร้าง order)"""
        return self.__basket
    
    # ===== เพิ่มใน class Order (ใกล้ๆ กับ update_status) =====

    def get_status(self) -> str: return self.__status
    def set_assigned_barista(self, barista):
        self.__assigned_barista = barista

    def get_assigned_barista(self):
        return self.__assigned_barista
    
    # 🆕 บันทึกว่าหักจากที่ไหน
    def set_stock_source(self, product_id: str, source: str):
        for ss in self.__stock_source:
            if ss.get_product_id() == product_id:
                ss.set_source(source)
                return
        self.__stock_source.append(StockSource(product_id, source))


    def get_stock_source(self, product_id: str) -> str:
        for ss in self.__stock_source:
            if ss.get_product_id() == product_id:
                return ss.get_source()
        return "warehouse"




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

    # --- แก้ไข calculate_total ให้รองรับกรณีที่ยังไม่มี Rider ---
    def calculate_total(self, vehicle=None) -> float:
        base_total = super().calculate_total()
        
        # หากยังไม่ได้รับมอบหมายรถ ให้คิดเรทมาตรฐานไปก่อน (20 + กม.ละ 10 บาท)
        if vehicle:
            self.__delivery_fee = vehicle.calculate_delivery_fee(self.__delivery_distance_km)
        else:
            self.__delivery_fee = 20.0 + (self.__delivery_distance_km * 10.0)

        # เช็คส่วนลดค่าส่งจาก Tier ของ Member
        if isinstance(self.get_customer(), Member):
            free_km = self.get_customer().get_tier().get_free_delivery_km()
            if self.__delivery_distance_km <= free_km:
                self.__delivery_fee = 0.0
                
        self.set_total_price(base_total + self.__delivery_fee)
        return self.get_total_price()
    
    def assign_rider(self, rider):
        self.__assigned_rider = rider

    def get_delivery_fee(self) -> float:
        return self.__delivery_fee
    # --- เพิ่ม Getter สำหรับให้เช็คได้ว่ามีคนรับงานหรือยัง ---
    def get_assigned_rider(self):
        return self.__assigned_rider
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 เพิ่มใหม่: ปลด Rider ออกจาก Order
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def unassign_rider(self):
        """ปลด Rider ออกจาก Order (ใช้ตอน Emergency Re-dispatch)"""
        old_rider = self.__assigned_rider
        self.__assigned_rider = None
        return old_rider


# --- Payment ---
class PaymentChannel:
    def __init__(self, channel_type: str):
        self.__channel_type = channel_type

    def get_channel_type(self) -> str:
        return self.__channel_type


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

class CODPayment(PaymentChannel):
    def __init__(self):
        super().__init__("COD")


class Payment:
    def __init__(self, order, payment_channel: PaymentChannel, amount: float):
        self.__order = order
        self.__payment_channel = payment_channel
        self.__amount = amount
        self.__status = "Pending"
        self.__timestamps = datetime.now()

    def set_status(self, status: str):
        self.__status = status
    
    def is_paid(self):
        return self.__status == "Success"
    def get_status(self) -> str:
        return self.__status
    
    # ✅ เพิ่ม 2 method ที่ขาดไป (create_transaction เรียกใช้)
    def get_payment_channel(self) -> PaymentChannel:
        return self.__payment_channel

    # transaction.py — เพิ่มใน class Payment (ต่อจาก get_payment_amount)

    def refund(self, customer, amount: float):
        """คืนเงินให้ลูกค้า"""
        if isinstance(customer, Customer):
            customer.receive_refund(amount)
        return True
    def get_amount(self) -> float:
        return self.__amount

    def make_payment(self, amount: float) -> bool:
        if amount >= self.__amount:
            self.__status = "Success"
            return True
        return False


# ==========================================
# --- Transaction & Receipt (เพิ่มใหม่) ---
# ==========================================
# ... (โค้ดเดิมใน transaction.py) ...

class Transaction:
    def __init__(self, staff, order, payment_channel: str):
        self.__transaction_id = str(uuid.uuid4())
        self.__staff = staff
        self.__order = order
        self.__payment_channel = payment_channel
        self.__amount = order.get_payment().get_amount()  # ✅ ดึงยอดที่ชำระจริง แทนการ calculate ซ้ำ
        self.__created_at = datetime.now()
        self.__status = "Completed"  # ← เพิ่มใหม่
    # --- Getters เดิม + ใหม่ ---
    def get_transaction_id(self) -> str:          # ← เพิ่มใหม่
        return self.__transaction_id

    def get_order(self):                           # ← เพิ่มใหม่
        return self.__order

    def get_staff(self):                           # ← เพิ่มใหม่
        return self.__staff

    def get_status(self) -> str:                   # ← เพิ่มใหม่
        return self.__status

    def update_status(self, status: str):          # ← เพิ่มใหม่
        self.__status = status
    
    # --- Void-related Methods (ย้ายมาจาก api-void.py) ---
    def void_related_order(self):
        """Void ออเดอร์ที่ผูกกับ Transaction นี้ + คืนเงิน"""
        # T->>O: update_status("Voided")
        self.__order.update_status("Voided")
        # T->>O: process_refund()
        self.__order.process_refund()
        return True


    # --- Receipt เดิม (คงไว้) ---
    def generate_receipt(self) -> str:
        customer = self.__order.get_customer()
        basket = self.__order.get_basket()
        items = basket.get_basket_items()

        receipt = (
            f"╔═════════════════════════════════════════╗\n"
            f"║     🧾 ใบเสร็จรับเงิน / RECEIPT        ║\n"
            f"║        ร้านบางกอน67                     ║\n"
            f"╠═════════════════════════════════════════╣\n"
            f"║ Transaction ID: {self.__transaction_id}\n"
            f"║ Order ID      : {self.__order.get_order_id()}\n"
            f"║ Order Type    : {self.__order.get_order_type()}\n"
            f"║ Date          : {self.__created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"╠═════════════════════════════════════════╣\n"
            f"║ 👤 ลูกค้า: {customer.get_name()}\n"
        )

        from person import Member
        if isinstance(customer, Member):
            receipt += (
                f"║    เบอร์โทร : {customer.get_my_phone()}\n"
                f"║    Tier     : {customer.get_tier().get_tier_name()}\n"
                f"║    แต้มสะสม : {customer.get_point()} แต้ม\n"
            )

        receipt += (
            f"╠═════════════════════════════════════════╣\n"
            f"║ 👨‍💼 พนักงาน: {self.__staff.get_name()} ({self.__staff.get_employee_id()})\n"
            f"╠═════════════════════════════════════════╣\n"
            f"║ 🛒 รายการสินค้า:\n"
        )

        sub_total = 0.0
        for i, item in enumerate(items, 1):
            product = item.get_product_order_item()
            qty = item.get_qty()
            price = product.get_price()
            line_total = price * qty
            sub_total += line_total
            receipt += f"║   {i}. {product.get_name():<20s} x{qty}  @{price:.0f}  = {line_total:.2f} บาท\n"

        receipt += f"╠═════════════════════════════════════════╣\n"
        receipt += f"║   ยอดรวมสินค้า           : {sub_total:.2f} บาท\n"

        if isinstance(customer, Member):
            discount_rate = customer.get_tier().get_discount_rate()
            if discount_rate > 0:
                discount_amount = sub_total * discount_rate
                receipt += f"║   ส่วนลดสมาชิก ({discount_rate*100:.0f}%)    : -{discount_amount:.2f} บาท\n"

        from transaction import OnlineOrder
        if isinstance(self.__order, OnlineOrder):
            delivery_fee = self.__order.get_delivery_fee()
            receipt += f"║   ค่าจัดส่ง              : {delivery_fee:.2f} บาท\n"

        receipt += (
            f"╠═════════════════════════════════════════╣\n"
            f"║   💰 ยอดชำระทั้งสิ้น     : {self.__amount:.2f} บาท\n"
            f"║   💳 ช่องทางชำระ         : {self.__payment_channel}\n"
            f"╠═════════════════════════════════════════╣\n"
        )

        barista = self.__order.get_assigned_barista()
        if barista:
            receipt += f"║ ☕ Barista: {barista.get_name()} ({barista.get_employee_id()})\n"

        if isinstance(self.__order, OnlineOrder):
            rider = self.__order.get_assigned_rider()
            if rider:
                receipt += f"║ 🏍️ Rider : {rider.get_name()} ({rider.get_license_plate()})\n"

        receipt += (
            f"╠═════════════════════════════════════════╣\n"
            f"║       ขอบคุณที่ใช้บริการร้านบางกอน67      ║\n"
            f"║          Thank you for your visit!       ║\n"
            f"╚═════════════════════════════════════════╝\n"
        )
        return receipt

# transaction.py — เพิ่มต่อท้ายไฟล์ (หลัง class Transaction)

class VoidTransaction(Transaction):
    """บันทึกการยกเลิก Transaction เดิม"""
    def __init__(self, original_transaction: Transaction, void_reason: str, staff):
        # เรียก super().__init__ โดยใช้ order เดิมจาก transaction ที่ถูก void
        super().__init__(staff, original_transaction.get_order(), "VOID")
        self.__original_transaction = original_transaction
        self.__void_reason = void_reason
        self.__voided_by = staff
        self.__void_timestamp = datetime.now()

    def get_original_transaction(self):
        return self.__original_transaction

    def get_void_reason(self) -> str:
        return self.__void_reason

    def generate_void_receipt(self) -> str:
        order = self.get_order()
        customer = order.get_customer()
        original_payment = order.get_payment()
        basket = order.get_basket()
        items = basket.get_basket_items()

        receipt = (
            f"╔═════════════════════════════════════════╗\n"
            f"║    ❌ ใบยกเลิกรายการ / VOID RECEIPT     ║\n"
            f"║           ร้านบางกอน67                  ║\n"
            f"╠═════════════════════════════════════════╣\n"
            f"║ Void Transaction ID : {self.get_transaction_id()}\n"
            f"║ Original Txn ID     : {self.__original_transaction.get_transaction_id()}\n"
            f"║ Order ID            : {order.get_order_id()}\n"
            f"║ Void Date           : {self.__void_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"╠═════════════════════════════════════════╣\n"
            f"║ 👤 ลูกค้า : {customer.get_name()}\n"
            f"║ 👨‍💼 Void โดย: {self.__voided_by.get_name()} ({self.__voided_by.get_employee_id()})\n"
            f"║ 📋 เหตุผล : {self.__void_reason}\n"
            f"╠═════════════════════════════════════════╣\n"
            f"║ 🛒 สินค้าที่คืน Stock:\n"
        )

        for i, item in enumerate(items, 1):
            product = item.get_product_order_item()
            qty = item.get_qty()
            price = product.get_price()
            receipt += f"║   {i}. {product.get_name():<20s} x{qty}  @{price:.0f}  = {price*qty:.2f} บาท\n"

        receipt += (
            f"╠═════════════════════════════════════════╣\n"
            f"║ 💰 จำนวนเงินที่คืน : {original_payment.get_amount():.2f} บาท\n"
            f"║ 📦 สินค้าทั้งหมดคืน Stock เรียบร้อย\n"
        )

        from person import Member
        if isinstance(customer, Member):
            earned_points = order.calculate_member_point()
            receipt += f"║ ⭐ หักแต้มคืน       : {earned_points} แต้ม\n"

        receipt += (
            f"╠═════════════════════════════════════════╣\n"
            f"║     รายการนี้ถูกยกเลิกเรียบร้อยแล้ว       ║\n"
            f"║        This transaction is voided.       ║\n"
            f"╚═════════════════════════════════════════╝\n"
        )
        return receipt

