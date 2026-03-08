from basket import Basket, OrderItem
from notification import SMSNotification, SystemNotification


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
        self.__refunded_total = 0.0  # ← เพิ่มบรรทัดนี้ใน __init__

    def get_basket(self) -> Basket:
        return self.__basket

    def add_to_basket(self, new_order_item: OrderItem) -> bool:
        self.__basket.add_to_basket(new_order_item)
        return True

    def clear_basket(self):
        self.__basket = Basket()

    def receive_refund(self, amount: float):
        """รับเงินคืนจากการ Void Transaction"""
        self.__refunded_total += amount
        return True

    def get_refunded_total(self) -> float:
        return self.__refunded_total



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
class Member(Customer):
    def __init__(self, phone: str, name: str = "Member Customer", age: int = 0, address: str = "", distance_km: float = 0.0, password: str = ""):
        super().__init__(name, age)
        self.__phone = phone
        self.__password = password 
        self.__point = 0
        self.__address = address
        self.__distance_km = distance_km
        self.__current_tier = StandardTier()
        self.__transaction_history = []

    def get_my_phone(self): return self.__phone
    def get_tier(self) -> MemberShipTier: return self.__current_tier
    def get_address(self) -> str: return self.__address
    def get_distance_km(self) -> float: return self.__distance_km

    def received_point(self, point: int) -> bool:
        self.__point += point
        self._check_tier_upgrade()
        return True

    def get_point(self) -> int: return self.__point

    def _check_tier_upgrade(self):
        if self.__point >= 1000:
            if not isinstance(self.__current_tier, GoldTier):
                self.__current_tier = GoldTier()
        elif self.__point >= 250:
            if not isinstance(self.__current_tier, SilverTier):
                self.__current_tier = SilverTier()

    # ✅ เพิ่ม 2 method นี้
    def add_transaction_history(self, transaction):
        self.__transaction_history.append(transaction)

    def get_transaction_history(self) -> list:
        return self.__transaction_history
    def verify_password(self, password: str) -> bool:
        """ตรวจสอบรหัสผ่าน"""
        return self.__password == password

    def deduct_points(self, points: int):
        """หักแต้มคืน (ใช้ตอน Void)"""
        self.__point = max(0, self.__point - points)
    
# --- Employee ---
class Employee(Person):
    def __init__(self, employee_id: str, name: str, age: int):
        super().__init__(name, age)
        self.__employee_id = employee_id

    def get_employee_id(self): return self.__employee_id

# --- ให้วางต่อจากคลาส Employee (ประมาณบรรทัด 137) ---
class Rider(Employee):
    def __init__(self, employee_id: str, name: str, age: int, license_plate: str, rate_per_km: float = 10.0):
        super().__init__(employee_id, name, age)
        self.__license_plate = license_plate
        self.__rate_per_km = rate_per_km
        self.__is_available = True
        self.__emergency_status = None  # 🔧 แก้ Bug: ต้อง init ไว้ ไม่งั้น get ก่อน set จะ Error

    def get_license_plate(self): return self.__license_plate
    def is_available(self): return self.__is_available
    def set_available(self, status: bool): self.__is_available = status

    def calculate_delivery_fee(self, distance_km: float) -> float:
        # คิดค่าส่งเริ่มต้น 20 บาท + (กิโลเมตรละ * เรท)
        return 20.0 + (distance_km * self.__rate_per_km)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 เพิ่มใหม่: Emergency Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def report_emergency(self, reason: str) -> bool:
        """Rider แจ้งเหตุฉุกเฉิน — ตั้ง flag ว่ากำลังมีปัญหา"""
        self.__emergency_status = reason
        self.__is_available = False  # ยังไม่ว่าง (อยู่ระหว่างจัดการเหตุ)
        return True

    def get_emergency_status(self) -> str:
        return self.__emergency_status

    def clear_emergency(self):
        """เคลียร์สถานะฉุกเฉิน (Staff เรียกหลังจัดการเสร็จ)"""
        self.__emergency_status = None
        self.__is_available = True
        
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
    def remove_order(self, order_items: list):
        """ลบ order items ออกจาก barista slot (ใช้เมื่อ Void)"""
        for item in order_items:
            if item in self.__order_drinks:
                self.__order_drinks.remove(item)
        if self.get_current_load() < self.__max_drink_slot:
            self.__status = "available"


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
    # ✅ เพิ่ม method ใหม่
    def remove_drinks(self, order_items: list):
        """ปลดเครื่องดื่มออกจากคิว (ใช้ตอน Void)"""
        self.__barista_slot.remove_order(order_items)

# --- Staff ---
class Staff(Employee):
    def __init__(self, employee_id: str, name: str, age: int = 0, admin_level: int = 1):
        super().__init__(employee_id, name, age)
        self.__admin_level = admin_level

    def get_admin_level(self) -> int: 
        return self.__admin_level

    # ตรงกับ SC->>S: validate_admin() ใน api-void.py
    def validate_admin(self) -> bool:
        # กำหนดเกณฑ์: สมมติให้ admin_level ตั้งแต่ 2 ขึ้นไป ถือว่ามีสิทธิ์ระดับ Admin (เช่น ทำการ Void ได้)
        # Level 1 = พนักงานทั่วไป (Cashier)
        # Level 2 = ผู้จัดการ (Manager)
        # Level 3 = เจ้าของร้าน (Owner)
        return self.__admin_level >= 2
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 เพิ่มใหม่: จัดการ alert ฉุกเฉิน
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔄 แก้ไข: handle_alert ส่ง 2 Notification
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def handle_alert(self, order_id: str, rider_name: str,
                     reason: str, customer_phone: str = "") -> dict:
        """
        Staff รับแจ้งเหตุฉุกเฉิน แล้วส่ง Notification 2 ทาง:
          1. SystemNotification → แจ้งระบบ/Staff ทุกคน
          2. SMSNotification   → แจ้งลูกค้าเจ้าของออเดอร์
        """

        # ─── 1. แจ้งระบบ (Staff/Admin เห็นบน Dashboard) ───
        sys_notifier = SystemNotification()
        sys_message = (
            f"🚨 EMERGENCY ALERT\n"
            f"   Order: {order_id}\n"
            f"   Rider: {rider_name}\n"
            f"   Reason: {reason}\n"
            f"   Action Required: Re-dispatch"
        )
        sys_status = sys_notifier.send(sys_message)

        # ─── 2. แจ้งลูกค้าทาง SMS (ถ้ามีเบอร์โทร) ───
        sms_status = "no_phone"
        if customer_phone:
            sms_notifier = SMSNotification(customer_phone)
            sms_message = (
                f"แจ้งเตือนจากร้านบางกอน67: "
                f"ออเดอร์ {order_id} ของคุณกำลังถูกจัดส่งใหม่ "
                f"เนื่องจากผู้จัดส่งมีเหตุฉุกเฉิน ({reason}) "
                f"ขออภัยในความไม่สะดวกครับ"
            )
            sms_status = sms_notifier.send(sms_message)

        return {
            "handled_by": self.get_name(),
            "staff_id": self.get_employee_id(),
            "system_notification": sys_status,
            "sms_notification": sms_status
        }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 เติมสินค้าจากคลังไปชั้นวาง
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def refill_shelf(self, shelf_slot, warehouse_stock) -> str:
        """
        Staff ดำเนินการเติมสินค้า (เรียกหลังได้รับ Notification):
          1. เช็คชั้นวาง → check_stock_level()
          2. คำนวณจำนวนที่ต้องเติม
          3. สั่ง Warehouse โอนสินค้า → transfer_to_shelf()
        """
        # 1. เช็คสต็อกบนชั้น
        current_qty, capacity, product = shelf_slot.check_stock_level()

        # 2. คำนวณ
        qty_to_refill = capacity - current_qty
        if qty_to_refill <= 0:
            return "ALREADY_FULL"

        # 3. สั่ง Warehouse โอน
        transfer_success = warehouse_stock.transfer_to_shelf(
            product, qty_to_refill, shelf_slot
        )

        if not transfer_success:
            return "STATUS_FAILED"

        return "REFILL_COMPLETED"