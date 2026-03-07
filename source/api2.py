from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# ==========================================
# 1. Models & Participants (Classes)
# ==========================================

class RefillRequest(BaseModel):
    staff_id: str
    slot_id: str

class Product:
    def __init__(self, product_id: str, name: str, stock_qty: int):
        self.__product_id = product_id
        self.__name = name
        self.__stock_qty = stock_qty  # จำนวนสต็อกในโกดังหลัก

    def get_name(self):
        return self.__name

    def get_stock_qty(self):
        return self.__stock_qty

    def deduct_stock(self, qty: int) -> bool:
        """ 6. Warehouse เรียกตัดสต็อกจาก Product Object """
        if self.__stock_qty >= qty:
            self.__stock_qty -= qty
            print(f"   📦 [Product] ตัดสต็อก {self.__name} สำเร็จ! เหลือในคลัง: {self.__stock_qty}")
            return True
        else:
            print(f"   ❌ [Product] สต็อก {self.__name} ในคลังไม่พอ! (ต้องการ: {qty}, มีแค่: {self.__stock_qty})")
            return False

class ShelfSlot:
    def __init__(self, slot_id: str, capacity: int, current_qty: int, product_obj: Product):
        self.__slot_id = slot_id
        self.__capacity = capacity
        self.__current_qty = current_qty
        self.__product_obj = product_obj

    def get_slot_id(self):
        return self.__slot_id

    def check_stock_level(self):
        """ 4. Staff ถาม ShelfSlot ว่ามีของเหลือเท่าไหร่ """
        print(f"   🔍 [ShelfSlot] เช็คชั้นวาง {self.__slot_id} ปัจจุบันมี {self.__current_qty}/{self.__capacity}")
        return self.__current_qty, self.__capacity, self.__product_obj

    def add_product(self, product_obj: Product, qty: int):
        """ 7. คลังสั่งเอาของไปเพิ่มใน ShelfSlot Object """
        self.__current_qty += qty
        print(f"   🛒 [ShelfSlot] นำ {product_obj.get_name()} เติมเข้าชั้นวาง {qty} ชิ้น (อัปเดต: {self.__current_qty}/{self.__capacity})")
        return True

class WarehouseStock:
    def __init__(self):
        self.__product_list = [] # เพิ่ม List เก็บสินค้าตาม Class Diagram

    def add_product(self, product: Product):
        self.__product_list.append(product)
        print(f"   🏠 [Warehouse] ลงทะเบียนสินค้า {product.get_name()} เข้าโกดังแล้ว (จำนวน: {product.get_stock_qty()})")

    def transfer_to_shelf(self, product_obj: Product, qty_to_refill: int, shelf_slot_obj: ShelfSlot) -> bool:
        """ 5. Staff สั่ง Warehouse ให้โอนสินค้า """
        # 6. Warehouse เรียกตัดสต็อกจาก Product Object
        is_enough = product_obj.deduct_stock(qty_to_refill)

        # alt not enough
        if not is_enough:
            return False
            
        # else enough
        # 7. คลังตัดของสำเร็จ ก็สั่งเอาของไปเพิ่มใน ShelfSlot Object
        shelf_slot_obj.add_product(product_obj, qty_to_refill)
        return True

class Staff:
    def __init__(self, staff_id: str, name: str):
        self.__staff_id = staff_id
        self.__name = name

    def get_staff_id(self):
        return self.__staff_id

    def get_name(self):
        return self.__name

    def refill_shelf(self, shelf_slot_obj: ShelfSlot, warehouse_stock: WarehouseStock):
        """ 3. Staff เริ่มทำงานกับ Object ที่ได้รับมา """
        print(f"\n--- 👨‍🔧 Staff {self.__name} กำลังดำเนินการเติมสินค้า ---")
        
        # 4. Staff เช็คสต็อกบนชั้น
        current_qty, capacity, product_obj = shelf_slot_obj.check_stock_level()
        
        qty_to_refill = capacity - current_qty
        if qty_to_refill <= 0:
            return "ALREADY_FULL"

        print(f"   💡 [Staff] คำนวณแล้วว่าต้องเติม {product_obj.get_name()} จำนวน {qty_to_refill} ชิ้น")

        # 5. Staff สั่ง Warehouse ให้โอนสินค้า
        transfer_success = warehouse_stock.transfer_to_shelf(product_obj, qty_to_refill, shelf_slot_obj)

        if not transfer_success:
            return "STATUS_FAILED"
            
        return "REFILL_COMPLETED"

class ShopController:
    def __init__(self):
        self.__employees = []
        self.__shelf_slots = []
        self.__warehouse_stock = WarehouseStock() # สร้างโกดังพร้อมกับร้าน

    # --- Setup Data Methods ---
    def add_employee(self, staff: Staff):
        self.__employees.append(staff)

    def add_shelf_slot(self, slot: ShelfSlot):
        self.__shelf_slots.append(slot)

    def get_warehouse_stock(self) -> WarehouseStock:
        return self.__warehouse_stock

    # --- Working Methods ---
    def get_employee_by_id(self, staff_id: str) -> Staff:
        for emp in self.__employees:
            if emp.get_staff_id() == staff_id:
                return emp
        return None

    def find_shelf_slot(self, slot_id: str) -> ShelfSlot:
        for slot in self.__shelf_slots:
            if slot.get_slot_id() == slot_id:
                return slot
        return None

    def refill_shelf_from_warehouse(self, staff_id: str, slot_id: str):
        """ 1. Actor สั่งงานผ่านระบบหน้าร้านมายัง ShopController """
        
        staff_obj = self.get_employee_by_id(staff_id)
        if not staff_obj:
            raise HTTPException(status_code=404, detail="Staff Not Found")

        shelf_slot_obj = self.find_shelf_slot(slot_id)
        if not shelf_slot_obj:
            raise HTTPException(status_code=404, detail="Shelf Slot Not Found")

        # 3. ส่ง Object ให้ Staff ทำงาน
        result_status = staff_obj.refill_shelf(shelf_slot_obj, self.__warehouse_stock)

        # จัดการผลลัพธ์ตาม Sequence Diagram (alt not enough / enough)
        if result_status == "STATUS_FAILED":
            raise HTTPException(status_code=400, detail="Warehouse Out of Stock")
        elif result_status == "ALREADY_FULL":
            return {"status": "Info", "message": "Shelf is already full"}
        elif result_status == "REFILL_COMPLETED":
            return {"status": "Success", "message": "Refill Successful"}


# ==========================================
# 2. Web / Setup Initial Data
# ==========================================
shop = ShopController()

# 🟢 CASE 1: ของในโกดังพอ (Success Case)
coke = Product("DR-01", "Coke Zero", stock_qty=100) # โกดังมี 100
shop.get_warehouse_stock().add_product(coke)

slot_a1 = ShelfSlot("SLOT-A1", capacity=20, current_qty=5, product_obj=coke) # ขาด 15 ชิ้น
shop.add_shelf_slot(slot_a1)


# 🔴 CASE 2: ของในโกดังไม่พอ (Fail Case)
pepsi = Product("DR-02", "Pepsi", stock_qty=10) # โกดังมีแค่ 10
shop.get_warehouse_stock().add_product(pepsi)

slot_a2 = ShelfSlot("SLOT-A2", capacity=30, current_qty=5, product_obj=pepsi) # ขาด 25 ชิ้น
shop.add_shelf_slot(slot_a2)


# สร้างพนักงาน
staff_somchai = Staff("EMP-01", "Somchai")
shop.add_employee(staff_somchai)

# ==========================================
# 3. API Endpoint
# ==========================================
@app.post("/api/inventory/refill")
def api_refill_shelf(request: RefillRequest):
    return shop.refill_shelf_from_warehouse(request.staff_id, request.slot_id)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)