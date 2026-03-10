from datetime import datetime, time
from fastmcp import FastMCP
import secrets

# ==========================================
# 1. Init MCP Server
# ==========================================
mcp = FastMCP("Shop_Bang_Korn_67_System")

# ==========================================
# 2. Classes & Participants (OOP Models)
# ==========================================

# --- Product Hierarchy ---
class Product:
    def __init__(self, product_id, name, price, stock_qty):
        self.__product_id = product_id
        self.__name = name
        self.__price = price
        self.__stock_qty = stock_qty

    def get_price(self): return self.__price
    def get_product_id(self): return self.__product_id
    def get_name(self): return self.__name
    def get_qty(self): return self.__stock_qty

    def validate_alcohol(self) -> bool:
        return False

    def validate_cafe_drink(self) -> bool:
        return False

    def validate_sale_time(self, current_time: datetime) -> bool:
        t = current_time.time()
        if (time(11, 0) <= t <= time(14, 0)) or (time(17, 0) <= t <= time(23, 59, 59)):
            return True
        return False

    def is_available(self, qty: int) -> bool:
        if self.__product_id == "OUT" or qty > self.__stock_qty:
            return False
        return True


class NormalProduct(Product):
    pass


class AlcoholProduct(Product):
    def __init__(self, product_id, name, price, stock_qty, alcohol_percentage: str = "5%"):
        super().__init__(product_id, name, price, stock_qty)
        self.__alcohol_percentage = alcohol_percentage
        self.__restricted_age = 20

    def get_restricted_age(self) -> int:
        return self.__restricted_age

    def validate_alcohol(self) -> bool:
        return True


class IngredientProduct(Product):
    def __init__(self, product_id, name, price, stock_qty):
        super().__init__(product_id, name, price, stock_qty)


class CafeProduct(Product):
    def __init__(self, product_id, name, price, stock_qty):
        super().__init__(product_id, name, price, stock_qty)
        self.__size = ["S", "M", "L"]

    def validate_cafe_drink(self) -> bool:
        return True


# --- OrderItem ---
class OrderItem:
    def __init__(self, product: Product, qty):
        self.__product = product
        self.__qty = qty
        self.__unit_price = product.get_price()

    def get_qty(self): return self.__qty
    def get_product_order_item(self) -> Product: return self.__product


# --- Basket ---
class Basket:
    def __init__(self):
        self.__items = []

    def get_basket_items(self): return self.__items

    def create_order_item(self, product, qty):
        return OrderItem(product, qty)

    def add_to_basket(self, new_order_item: OrderItem) -> bool:
        self.__items.append(new_order_item)
        return True

    def count_drink_items(self) -> int:
        count = 0
        for item in self.__items:
            product = item.get_product_order_item()
            if product.validate_cafe_drink():
                count += item.get_qty()
        return count


# --- Person (Base) ---
class Person:
    def __init__(self, name: str, age: int):
        self.__name = name
        self.__age = age

    def get_name(self) -> str: return self.__name
    def get_age(self) -> int: return self.__age


# --- Customer ---
class Customer(Person):
    def __init__(self, name: str = "Guest", age: int = 0):
        super().__init__(name, age)
        self.__basket = Basket()

    def get_basket(self) -> Basket:
        return self.__basket

    def add_to_basket(self, new_order_item: OrderItem) -> bool:
        self.__basket.add_to_basket(new_order_item)
        return True

    def clear_basket(self):
        self.__basket = Basket()


# --- MemberShipTier Hierarchy ---
# [แก้ไข] เปลี่ยนจาก min_spending → min_points
class MemberShipTier:
    def __init__(self, tier: str, min_points: int, discount_rate: float, free_km: float):
        self.__tier = tier
        self.__min_points_to_upgrade = min_points
        self.__discount_rate = discount_rate
        self.__free_delivery_km = free_km

    def get_tier_name(self): return self.__tier
    def get_min_points(self): return self.__min_points_to_upgrade
    def get_discount_rate(self): return self.__discount_rate
    def get_free_delivery_km(self): return self.__free_delivery_km


class StandardTier(MemberShipTier):
    def __init__(self):
        # Standard: 0% discount, ไม่มี free delivery, สมัครใหม่
        super().__init__("Standard", 0, 0.0, 0.0)


class SilverTier(MemberShipTier):
    def __init__(self):
        # Silver: 3% discount, ไม่มี free delivery, ครบ 250 points
        super().__init__("Silver", 250, 0.03, 0.0)


class GoldTier(MemberShipTier):
    def __init__(self):
        # Gold: 5% discount, ฟรี 3 กม.แรก, ครบ 1000 points
        super().__init__("Gold", 1000, 0.05, 3.0)


# --- Member ---
# [แก้ไข] ลบ accumulated_spending, ใช้ point เป็นตัวตัดสิน tier
class Member(Customer):
    def __init__(self, phone: str, name: str = "Member Customer", age: int = 0):
        super().__init__(name, age)
        self.__phone = phone
        self.__point = 0
        self.__address = ""
        self.__current_tier = StandardTier()
        self.__transaction_history = []

    def get_my_phone(self): return self.__phone
    def get_tier(self) -> MemberShipTier: return self.__current_tier

    # [แก้ไข] received_point → เรียก _check_tier_upgrade หลังได้รับพอยต์
    def received_point(self, point: int) -> bool:
        self.__point += point
        self._check_tier_upgrade()
        return True

    def get_point(self) -> int: return self.__point

    # [แก้ไข] เช็ค tier จาก __point แทน __accumulated_spending
    def _check_tier_upgrade(self):
        if self.__point >= 1000:
            if not isinstance(self.__current_tier, GoldTier):
                self.__current_tier = GoldTier()
        elif self.__point >= 250:
            if not isinstance(self.__current_tier, SilverTier):
                self.__current_tier = SilverTier()


# --- Employee ---
class Employee(Person):
    def __init__(self, employee_id: str, name: str, age: int):
        super().__init__(name, age)
        self.__employee_id = employee_id

    def get_employee_id(self): return self.__employee_id


# --- BaristaSlot ---
class BaristaSlot:
    def __init__(self):
        self.__status = "available"
        self.__order_drinks = []
        self.__max_drink_slot = 10

    def get_current_load(self) -> int:
        return sum(item.get_qty() for item in self.__order_drinks)

    def can_accept(self, new_drinks_qty: int) -> bool:
        return (self.get_current_load() + new_drinks_qty) <= self.__max_drink_slot

    def add_order(self, order_items: list):
        for item in order_items:
            if item.get_product_order_item().validate_cafe_drink():
                self.__order_drinks.append(item)
        if self.get_current_load() >= self.__max_drink_slot:
            self.__status = "busy"


# --- Barista ---
class Barista(Employee):
    def __init__(self, employee_id: str, name: str, age: int = 0):
        super().__init__(employee_id, name, age)
        self.__barista_slot = BaristaSlot()

    def check_queue_barista(self) -> int:
        return self.__barista_slot.get_current_load()

    def can_accept_order(self, drinks_qty: int) -> bool:
        return self.__barista_slot.can_accept(drinks_qty)

    def assign_drinks(self, order_items: list):
        self.__barista_slot.add_order(order_items)


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


# --- ShopController ---
class ShopController:
    def __init__(self):
        self.__member = []
        self.__product = []
        self.__barista = []
        self.__current_guest = Customer()

    def get_member(self, phone_number: str):
        for member in self.__member:
            if member.get_my_phone() == phone_number:
                return member
        return None

    def get_member_by_phone(self, phone_number: str):
        return self.get_member(phone_number)

    def create_member(self, phone: str, name: str = "Member Customer"):
        self.__member.append(Member(phone, name))

    def add_product(self, product: Product):
        self.__product.append(product)

    def get_product(self):
        return self.__product

    def get_product_by_id(self, product_id: str):
        for product in self.__product:
            if product.get_product_id() == product_id:
                return product
        return None

    def add_barista(self, barista: Barista):
        self.__barista.append(barista)

    def get_barista(self):
        return self.__barista

    def get_current_guest(self) -> Customer:
        return self.__current_guest

    def reset_current_guest(self):
        self.__current_guest = Customer()

    def create_order(self, customer: Customer, order_type: str) -> OnsiteOrder:
        return OnsiteOrder(customer, order_type)

    def create_payment(self, order: Order, payment_channel: PaymentChannel, amount: float) -> Payment:
        return Payment(order, payment_channel, amount)


# ==========================================
# 3. Database Mock
# ==========================================
shop_bang_korn_67 = ShopController()
shop_bang_korn_67.add_barista(Barista("EMP-001", "John (Barista 1)"))

coke = NormalProduct("DR-001", "Coke", 20, 100)
coffee = CafeProduct("CF-001", "Iced Latte", 65, 100)
beer = AlcoholProduct("ALC-001", "Beer", 60, 100, alcohol_percentage="5%")
lay = NormalProduct("GD-001", "Lay", 45, 100)

shop_bang_korn_67.add_product(coke)
shop_bang_korn_67.add_product(coffee)
shop_bang_korn_67.add_product(beer)
shop_bang_korn_67.add_product(lay)

shop_bang_korn_67.create_member("0915919569", "คุณลูกค้า VIP")


# ==========================================
# 4. MCP Tools
# ==========================================

# [แก้ไข] ปรับ description ให้ AI รู้ว่าต้องเรียก tool นี้ก่อน process_payment เสมอ
@mcp.tool()
def add_product_to_basket(product_id: str, qty: int, phone_member: str) -> str:
    """
    [ขั้นตอนที่ 1 - ต้องเรียกก่อน process_payment เสมอ]
    ฟังก์ชันสำหรับให้ลูกค้าหยิบสินค้าใส่ตะกร้า
    ต้องส่ง:
    - product_id: รหัสสินค้า (เช่น "DR-001", "CF-001", "ALC-001", "GD-001")
    - qty: จำนวน
    - phone_member: เบอร์โทรสมาชิก

    สินค้าที่มีในร้าน:
    - DR-001: Coke (20 บาท)
    - CF-001: Iced Latte (65 บาท)
    - ALC-001: Beer (60 บาท) - ขายได้เฉพาะ 11:00-14:00 และ 17:00-24:00
    - GD-001: Lay (45 บาท)

    หมายเหตุ: ต้องเรียก tool นี้อย่างน้อย 1 ครั้ง ก่อนเรียก process_payment
    """
    member_obj = shop_bang_korn_67.get_member_by_phone(phone_member)
    if not member_obj:
        return "Error: ไม่พบเบอร์โทรสมาชิกนี้ในระบบ"
    basket = member_obj.get_basket()

    selected_product = shop_bang_korn_67.get_product_by_id(product_id)
    if not selected_product:
        return f"Error: ไม่พบสินค้าหมายเลข {product_id} ในร้าน"

    is_alcohol = selected_product.validate_alcohol()
    if is_alcohol:
        current_time = datetime.now()
        is_valid_time = selected_product.validate_sale_time(current_time)
        if not is_valid_time:
            return "Error: ไม่สามารถเพิ่มลงตะกร้าได้ เนื่องจากกฎหมายกำหนดให้ขายแอลกอฮอล์ได้เฉพาะ 11:00-14:00 และ 17:00-24:00 น. เท่านั้น"

    is_avail = selected_product.is_available(qty)
    if not is_avail:
        return "Error: สินค้ามีไม่เพียงพอ หรือหมดสต็อก"

    new_order_item = basket.create_order_item(selected_product, qty)
    success = basket.add_to_basket(new_order_item)

    if success:
        count = sum(item.get_qty() for item in basket.get_basket_items())
        return f"Success: เพิ่ม {selected_product.get_name()} จำนวน {qty} ชิ้น ลงตะกร้าของเบอร์ {phone_member} เรียบร้อยแล้ว (ปัจจุบันในตะกร้ามีสินค้าทั้งหมด {count} ชิ้น) — พร้อมชำระเงินได้โดยเรียก process_payment"


# [แก้ไข] ปรับ description ให้ AI รู้ว่าต้องเรียก add_product_to_basket ก่อน
@mcp.tool()
def process_payment(payment_channel: str, received_amount: float = 0.0, phone_number: str = "") -> str:
    """
    [ขั้นตอนที่ 2 - ต้องเรียก add_product_to_basket ก่อนเสมอ]
    ฟังก์ชันสำหรับชำระเงิน (Checkout)

    ข้อกำหนดสำคัญ: ห้ามเรียก tool นี้โดยตรง ต้องเรียก add_product_to_basket ก่อนอย่างน้อย 1 ครั้ง
    เพื่อให้มีสินค้าในตะกร้าก่อนจึงจะชำระเงินได้

    ต้องระบุ:
    - payment_channel: "QR" (สแกนจ่าย) หรือ "CASH" (เงินสด)
    - received_amount: จำนวนเงินที่รับมา (กรณีจ่ายเงินสด ถ้าจ่าย QR ปล่อยเป็น 0)
    - phone_number: เบอร์โทรศัพท์สมาชิก (ถ้าเป็นลูกค้าทั่วไป ให้ใส่ "")
    """
    if phone_number and phone_number.strip() != "":
        customer_obj = shop_bang_korn_67.get_member(phone_number)
        if not customer_obj:
            return f"Error: ไม่พบเบอร์โทรสมาชิก {phone_number} ในระบบ"
    else:
        customer_obj = shop_bang_korn_67.get_current_guest()

    basket = customer_obj.get_basket()
    items = basket.get_basket_items()

    # [แก้ไข] ข้อความ error ชัดเจนขึ้น — บังคับให้ AI เรียก add_product_to_basket ก่อน
    if not items:
        return "Error: ตะกร้าสินค้าว่างเปล่า — กรุณาเรียกใช้ tool 'add_product_to_basket' เพื่อเลือกสินค้าลงตะกร้าก่อน แล้วจึงเรียก process_payment อีกครั้ง"

    for item in items:
        product = item.get_product_order_item()
        if product.validate_alcohol():
            if not product.validate_sale_time(datetime.now()):
                return "Error: มีแอลกอฮอล์ในตะกร้า ไม่สามารถชำระเงินได้ (ขายได้เฉพาะ 11:00-14:00 และ 17:00-24:00 น.)"

    drink_count = basket.count_drink_items()
    if drink_count > 10:
        return "Error: สั่งเครื่องดื่มได้สูงสุด 10 แก้วต่อออเดอร์"

    assigned_barista = None
    if drink_count > 0:
        baristas = shop_bang_korn_67.get_barista()
        for barista in baristas:
            if barista.can_accept_order(drink_count):
                assigned_barista = barista
                break
        if not assigned_barista:
            return "Error: คิวบาริสต้าเต็ม ไม่สามารถรับออเดอร์เครื่องดื่มเพิ่มได้ในขณะนี้"

    new_order = shop_bang_korn_67.create_order(customer_obj, "ONSITE")
    total_price = new_order.calculate_total()

    if payment_channel.upper() == "QR":
        channel = QRPayment()
        payment = shop_bang_korn_67.create_payment(new_order, channel, total_price)
        qr_data = channel.generate_qr_code(total_price)
        payment.set_status("Success")
        payment_msg = f"สร้าง QR Code สำเร็จ (QR Data: {qr_data})"

    elif payment_channel.upper() == "CASH":
        channel = CashPayment(received_amount)
        payment = shop_bang_korn_67.create_payment(new_order, channel, total_price)
        try:
            change = channel.calculate_change(total_price)
            payment.set_status("Success")
            payment_msg = f"รับเงินสด {received_amount} บาท | เงินทอน {change} บาท"
        except ValueError as e:
            payment.set_status("Failed")
            return f"Error: ชำระเงินไม่สำเร็จ - {str(e)} (ยอดรวม {total_price} บาท แต่รับเงินมาเพียง {received_amount} บาท)"
    else:
        return "Error: ช่องทางการชำระเงินไม่ถูกต้อง (ต้องเป็น QR หรือ CASH เท่านั้น)"

    # ==========================================
    # Flow หลังชำระเงิน ตาม Sequence Diagram
    # ==========================================
    if new_order.check_payment_status():
        if assigned_barista:
            assigned_barista.assign_drinks(items)

        result_msg = f"Success: ชำระเงินสำเร็จ! ยอดรวม {total_price} บาท ({payment_msg})"

        if isinstance(customer_obj, Member):
            # shop → order.calculate_member_point() : 10 บาท = 1 point
            earned_points = new_order.calculate_member_point()

            # shop → member.received_point(point) → ภายในจะเรียก _check_tier_upgrade() อัตโนมัติ
            customer_obj.received_point(earned_points)

            # เคลียร์ตะกร้าหลังชำระเสร็จ
            customer_obj.clear_basket()

            result_msg += f"\n- สถานะ: สมาชิก (Member)"
            result_msg += f"\n- ชื่อ: {customer_obj.get_name()}"
            result_msg += f"\n- Tier: {customer_obj.get_tier().get_tier_name()}"
            result_msg += f"\n- ส่วนลด Tier: {customer_obj.get_tier().get_discount_rate() * 100}%"
            result_msg += f"\n- ได้รับพอยต์เพิ่ม: {earned_points} แต้ม"
            result_msg += f"\n- พอยต์สะสมทั้งหมด: {customer_obj.get_point()} แต้ม"
            result_msg += f"\n- อัปเกรด Silver เมื่อครบ: 250 แต้ม"
            result_msg += f"\n- อัปเกรด Gold เมื่อครบ: 1,000 แต้ม"
        else:
            shop_bang_korn_67.reset_current_guest()
            result_msg += "\n- สถานะ: ลูกค้าทั่วไป (Guest)"

        return result_msg
    else:
        return "Error: การชำระเงินล้มเหลว"


# ==========================================
# 5. รันเซิร์ฟเวอร์ MCP
# ==========================================
if __name__ == "__main__":
    mcp.run()
