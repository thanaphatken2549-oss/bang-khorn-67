# warehouse.py
from notification import SystemNotification


class ShelfSlot:
    """ช่องชั้นวางสินค้า — มี threshold แจ้งเตือนเมื่อของน้อย"""

    def __init__(self, slot_id: str, capacity: int, current_qty: int,
                 product, min_threshold: int = 5):
        self.__slot_id = slot_id
        self.__capacity = capacity
        self.__current_qty = current_qty
        self.__product = product
        self.__min_threshold = min_threshold   # ← จุดสำคัญ!

    # --- Getters ---
    def get_slot_id(self) -> str: return self.__slot_id
    def get_capacity(self) -> int: return self.__capacity
    def get_current_qty(self) -> int: return self.__current_qty
    def get_product(self): return self.__product
    def get_min_threshold(self) -> int: return self.__min_threshold

    def check_stock_level(self) -> tuple:
        """Staff เรียก → ดูว่าเหลือเท่าไหร่ / จุเท่าไหร่ / สินค้าอะไร"""
        return self.__current_qty, self.__capacity, self.__product

    def is_below_threshold(self) -> bool:
        """WarehouseStock เรียก → เช็คว่าของต่ำกว่าเกณฑ์ไหม"""
        return self.__current_qty <= self.__min_threshold

    def add_product(self, qty: int) -> bool:
        """เพิ่มสินค้าเข้าชั้นวาง (WarehouseStock เรียกตอน transfer)"""
        self.__current_qty += qty
        if self.__current_qty > self.__capacity:
            self.__current_qty = self.__capacity
        return True
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 หักสต็อกเมื่อขายหน้าร้าน (ONSITE)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def deduct_qty(self, qty: int) -> bool:
        """หักของออกจากชั้นวาง เมื่อลูกค้าซื้อ ONSITE"""
        if self.__current_qty >= qty:
            self.__current_qty -= qty
            return True
        return False


class WarehouseStock:
    """
    คลังสินค้าหลัก — เป็นคนเก็บและดูแล ShelfSlot ทั้งหมด
    ทำหน้าที่:
      1. เก็บ shelf slots
      2. ตรวจสอบ stock level
      3. ส่ง Notification เมื่อพบของน้อย
      4. โอนสินค้าไปเติมชั้น
    """

    def __init__(self):
        self.__product_list = []
        self.__shelf_slots = []     # ← WarehouseStock เก็บ shelf ไว้เอง

    # --- จัดการสินค้า ---
    def add_product(self, product):
        self.__product_list.append(product)

    def get_product_list(self) -> list:
        return self.__product_list

    # --- จัดการชั้นวาง ---
    def add_shelf_slot(self, slot: ShelfSlot):
        self.__shelf_slots.append(slot)

    def find_shelf_slot(self, slot_id: str):
        for slot in self.__shelf_slots:
            if slot.get_slot_id() == slot_id:
                return slot
        return None

    def get_all_shelf_slots(self) -> list:
        return self.__shelf_slots
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 หักสต็อกจาก Shelf เมื่อขาย ONSITE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def deduct_from_shelf(self, product_id: str, qty: int) -> bool:
        """
        ค้นหา ShelfSlot ที่มีสินค้า product_id → หักออก
        ถูกเรียกจาก process_payment (ONSITE)
        """
        for slot in self.__shelf_slots:
            if slot.get_product().get_product_id() == product_id:
                return slot.deduct_qty(qty)
        return False  # ไม่พบ shelf ที่มีสินค้านี้

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 คืนสต็อกเข้า Shelf เมื่อ Void ONSITE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def restock_to_shelf(self, product_id: str, qty: int) -> bool:
        """คืนของเข้าชั้นวาง (ใช้ตอน Void)"""
        for slot in self.__shelf_slots:
            if slot.get_product().get_product_id() == product_id:
                return slot.add_product(qty)
        return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔑 หัวใจของระบบ: ตรวจ + แจ้งเตือนอัตโนมัติ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def check_and_notify_low_stock(self) -> list:
        """
        ตรวจสอบ ShelfSlot ทั้งหมดที่อยู่ในความดูแล
        ถ้าพบว่า current_qty <= min_threshold
        → ส่ง SystemNotification แจ้ง Staff
        → Return รายการชั้นที่ต้องเติม
        """
        low_stock_shelves = []
        sys_notifier = SystemNotification()

        for slot in self.__shelf_slots:
            if slot.is_below_threshold():
                product = slot.get_product()

                # ส่งแจ้งเตือนให้ Staff เห็นในระบบ
                message = (
                    f"⚠️ LOW STOCK ALERT\n"
                    f"   Shelf: {slot.get_slot_id()}\n"
                    f"   Product: {product.get_name()}\n"
                    f"   Current: {slot.get_current_qty()}/{slot.get_capacity()}\n"
                    f"   Threshold: {slot.get_min_threshold()}\n"
                    f"   Action: กรุณาเติมสินค้า (เรียก refill_shelf)"
                )
                noti_status = sys_notifier.send(message)

                low_stock_shelves.append({
                    "slot_id": slot.get_slot_id(),
                    "product_name": product.get_name(),
                    "current_qty": slot.get_current_qty(),
                    "capacity": slot.get_capacity(),
                    "threshold": slot.get_min_threshold(),
                    "need_refill": slot.get_capacity() - slot.get_current_qty(),
                    "notification_status": noti_status
                })

        return low_stock_shelves

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # โอนสินค้าจากคลัง → ชั้นวาง
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def transfer_to_shelf(self, product, qty_to_refill: int,
                          shelf_slot: ShelfSlot) -> bool:
        """
        ตัดสต็อกจาก Product (คลัง) แล้วเพิ่มเข้า ShelfSlot (ชั้นวาง)
        """
        if not product.is_available(qty_to_refill):
            return False

        product.deduct_stock(qty_to_refill)
        shelf_slot.add_product(qty_to_refill)
        return True
