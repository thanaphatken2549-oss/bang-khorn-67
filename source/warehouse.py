# warehouse.py
from notification import SystemNotification
from basket import Result


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


class IngredientStock:
    """เก็บสต็อกวัตถุดิบชงเครื่องดื่มในคลัง"""
    def __init__(self, ingredient, qty: int):
        self.__ingredient = ingredient
        self.__qty = qty

    def get_ingredient(self):
        return self.__ingredient

    def get_qty(self) -> int:
        return self.__qty

    def add_qty(self, amount: int):
        self.__qty += amount

    def deduct_qty(self, amount: int) -> bool:
        if self.__qty >= amount:
            self.__qty -= amount
            return True
        return False

class LowStockAlert:
    """แจ้งเตือนชั้นวางสินค้าที่ต่ำกว่าเกณฑ์"""
    def __init__(self, shelf_slot, notification_status: str):
        self.__shelf_slot = shelf_slot
        self.__notification_status = notification_status

    def get_shelf_slot(self): return self.__shelf_slot
    def get_notification_status(self): return self.__notification_status

    def get_need_refill(self) -> int:
        return self.__shelf_slot.get_capacity() - self.__shelf_slot.get_current_qty()


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
        self.__shelf_slots = []
        self.__ingredient_stock = []  # [(IngredientProduct, ...] 

    # --- จัดการสินค้า ---
    def add_product(self, product):
        self.__product_list.append(product)

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
        low_stock_shelves = []
        sys_notifier = SystemNotification()

        for slot in self.__shelf_slots:
            if slot.is_below_threshold():
                product = slot.get_product()
                message = (
                    f"⚠️ LOW STOCK ALERT\n"
                    f"   Shelf: {slot.get_slot_id()}\n"
                    f"   Product: {product.get_name()}\n"
                    f"   Current: {slot.get_current_qty()}/{slot.get_capacity()}\n"
                    f"   Threshold: {slot.get_min_threshold()}\n"
                    f"   Action: กรุณาเติมสินค้า (เรียก refill_shelf)"
                )
                noti_status = sys_notifier.send(message)
                low_stock_shelves.append(LowStockAlert(slot, noti_status))

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

    def add_ingredient_stock(self, ing, qty: int):
        for stock in self.__ingredient_stock:
            if stock.get_ingredient() == ing:
                stock.add_qty(qty)
                return
        self.__ingredient_stock.append(IngredientStock(ing, qty))

    def _get_ingredient_qty(self, ing) -> int:
        for stock in self.__ingredient_stock:
            if stock.get_ingredient() == ing:
                return stock.get_qty()
        return 0

    def check_ingredient(self, recipe, drink_qty: int = 1) -> bool:
        for ing in recipe.get_ingredients():
            per_cup = recipe.get_quantity_of_ingredient(ing)
            total_needed = per_cup * drink_qty
            if self._get_ingredient_qty(ing) < total_needed:
                return False
        return True


    def deduct_ingredient(self, ing, qty: int):
        for stock in self.__ingredient_stock:
            if stock.get_ingredient() == ing:
                if stock.deduct_qty(qty):
                    print(f"   🏭 [Warehouse] เบิก {ing.get_name()}: {qty} (เหลือ {stock.get_qty()})")
                    return True
        return False