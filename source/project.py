import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from datetime import datetime, timedelta
from fastmcp import FastMCP

from basket import Result
from product import Product, NormalProduct, CafeProduct, AlcoholProduct, IngredientProduct
from person import Customer, Member, Barista, Rider, Staff
from transaction import Order, OnsiteOrder, OnlineOrder, PaymentChannel, QRPayment, CashPayment, CODPayment, Payment, Transaction, VoidTransaction
from warehouse import ShelfSlot, WarehouseStock

# ... (โค้ด Mock Data เดิม) ...

# ==========================================
# 1. Classes & Participants (OOP Models)
# ==========================================



# --- ShopController ---
class ShopController:
    def __init__(self):
        self.__member = []
        self.__product = []
        self.__current_guest = Customer()
        self.__transactions = []
        self.__orders = []
        self.__employees = []
        self.__current_session = None 
        self.__warehouse_stock = WarehouseStock()   # 🆕 เพิ่มใหม่

    def get_member(self, phone_number: str):
        for member in self.__member:
            if member.get_my_phone() == phone_number:
                return member
        return None

    def create_member(self, phone: str, name: str = "Member Customer",password: str="", age=0, address: str = "", distance_km: float = 0.0):
        self.__member.append(
            Member(phone, name, age=age, address=address,
                    distance_km=distance_km, password=password)
        )

    def add_product(self, product: Product):
        self.__product.append(product)

    def get_product_by_id(self, product_id: str):
        for product in self.__product:
            if product.get_product_id() == product_id:
                return product
        return None
    
    def create_order(self, customer: Customer, order_type: str):
        if order_type == "ONLINE" and isinstance(customer, Member):
            payment_window = datetime.now() + timedelta(minutes=15)
            return OnlineOrder(
                customer,
                order_type,
                delivery_address=customer.get_address(),
                distance_km=customer.get_distance_km(),
                payment_window=payment_window
            )
        return OnsiteOrder(customer, order_type)

    def create_payment(self, order: Order, payment_channel: PaymentChannel, amount: float) -> Payment:
        return Payment(order, payment_channel, amount)
    
    def add_transaction(self, transaction):
        self.__transactions.append(transaction)
    # [เพิ่มใหม่ 3 ฟังก์ชันนี้ เข้าไปใน ShopController]
    def add_order(self, order: Order):
        self.__orders.append(order)

    def get_order_by_id(self, order_id: str) -> Order:
        for order in self.__orders:
            if order.get_order_id() == order_id:
                return order
        return None

    # ✅ เพิ่มพนักงานทุกประเภทด้วยฟังก์ชันเดียว
    def add_employee(self, employee):
        self.__employees.append(employee)

    # ✅ รวม get ทุกแบบไว้ในฟังก์ชันเดียว
    #    - ส่ง employee_id → คืน Employee ตัวเดียว (หรือ None)
    #    - ส่ง role        → คืน list ของพนักงานประเภทนั้น
    def get_employee(self, employee_id: str = None, role=None):
        if employee_id:
            for emp in self.__employees:
                if emp.get_employee_id() == employee_id:
                    return emp
            return None
        if role:
            return [emp for emp in self.__employees if isinstance(emp, role)]
        return self.__employees

    # ✅ ค้นหา Rider ที่ว่างอยู่ (business logic เฉพาะ)
    def get_available_rider(self):
        for rider in self.get_employee(role=Rider):
            if rider.is_available():
                return rider
        return None
    
    # project.py — เพิ่มใน class ShopController (ต่อจา)ก get_available_rider)

    def get_transaction_by_id(self, transaction_id: str):
        """ค้นหา Transaction จาก ID"""
        for t in self.__transactions:
            if t.get_transaction_id() == transaction_id:
                return t
        return None

    def create_voidtransaction(self, transaction: Transaction, void_reason: str, staff) -> VoidTransaction:
        """สร้าง VoidTransaction record"""
        return VoidTransaction(transaction, void_reason, staff)
    
    # ===== เพิ่มใน class ShopController (ต่อจาก get_available_rider) =====

    def get_pending_delivery_orders(self) -> list:
        """ค้นหา Online Order ทั้งหมดที่รอ Rider มารับงาน"""
        pending = []
        for order in self.__orders:
            if (isinstance(order, OnlineOrder)
                and order.get_status() == "Waiting for Rider"
                and order.get_assigned_rider() is None):
                pending.append(order)
        return pending
    
    def register_member(self, phone: str, name: str, password: str,age: int = 0, address: str = "", distance_km: float = 0.0):

        """สมัครสมาชิกใหม่ — ถ้าเบอร์ซ้ำ return None"""
        if self.get_member(phone):
            return None
        new_member = Member(phone, name, age=age, address=address,distance_km=distance_km, password=password)
        self.__member.append(new_member)
        return new_member

    def login_member(self, phone: str, password: str):
        """Login สมาชิก — สำเร็จ return Member, ไม่สำเร็จ return None"""
        member = self.get_member(phone)
        if member and member.verify_password(password):
            self.__current_session = member
            return member
        return None

    def login_guest(self):
        """Login แบบ Guest — ไม่ต้องใส่อะไร"""
        guest = Customer()
        self.__current_session = guest
        return guest

    def logout(self):
        """Logout — ล้าง session"""
        self.__current_session = None

    def get_current_session(self):
        """ดึง user ที่ login อยู่ (Member หรือ Guest Customer หรือ None)"""
        return self.__current_session

    def is_logged_in(self) -> bool:
        return self.__current_session is not None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 เพิ่มใหม่: Emergency Report Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def find_order_by_rider(self, rider_id: str):
        """ค้นหา Online Order ที่ Rider คนนี้กำลังส่งอยู่"""
        for order in self.__orders:
            if (isinstance(order, OnlineOrder)
                and order.get_status() == "Delivering"
                and order.get_assigned_rider() is not None
                and order.get_assigned_rider().get_employee_id() == rider_id):
                return order
        return None

    def find_available_staff(self):
        """ค้นหา Staff ที่สามารถรับเรื่องได้ (auto-assign)"""
        staff_list = self.get_employee(role=Staff)
        if staff_list:
            return staff_list[0]  # เอาคนแรกที่เจอ
        return None

    def report_emergency(self, rider_id: str, reason: str) -> dict:
        """
        Rider แจ้งเหตุฉุกเฉิน — ระบบจัดการ Re-dispatch
        ตรงกับ Sequence Diagram ใน can2.py:
          1. Rider → ShopController: report_emergency()
          2. SC → SC: get_staffid() (self-call)
          3. SC → Staff: handle_alert()
          4. Staff → Notification: send()
          5. Notification → Staff: success
          6. Staff → SC: success
          7. SC → SC: get_orderid() (self-call)
          8. SC → Order: update_status("Re-dispatch")
          9. Order → Order: self-call update
         10. Order → SC: success
         11. SC → Rider: success
        """

        # [Seq 1] รับแจ้งจาก Rider
        rider = self.get_employee(rider_id)
        if not rider or not isinstance(rider, Rider):
            return Result("error", f"ไม่พบ Rider ID: {rider_id}")

        order = self.find_order_by_rider(rider_id)
        if not order:
            return Result("error", f"Rider {rider_id} ไม่มี Order ที่กำลังส่งอยู่")

        staff = self.find_available_staff()
        if not staff:
            return Result("error", "ไม่พบ Staff ในระบบ")

         # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🆕 ดึงเบอร์ลูกค้าจาก Order เพื่อส่ง SMS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        customer = order.get_customer()
        customer_phone = ""
        if isinstance(customer, Member):
            customer_phone = customer.get_my_phone()

        # Rider ตั้ง flag emergency
        rider.report_emergency(reason)

        # [Seq 3-6] Staff → handle_alert (ส่ง Notification ทั้ง 2 ทาง)
        alert_result = staff.handle_alert(
            order.get_order_id(),
            rider.get_name(),
            reason,
            customer_phone=customer_phone   # 🆕 ส่งเบอร์ลูกค้าเข้าไปด้วย
        )


        # [Seq 7] SC → SC: get_orderid() (self-call)
        # (order ถูกค้นหาไว้แล้วข้างบน)

        order.unassign_rider()
        order.update_status("Waiting for Rider")

        result = Result("success")
        result.set_extra("order_id", order.get_order_id())
        result.set_extra("new_order_status", "Waiting for Rider (Re-dispatch)")
        result.set_extra("handled_by", alert_result.get_extra("handled_by"))
        result.set_extra("rider_released", rider.get_name())
        result.set_extra("reason", reason)
        result.set_extra("system_notification", alert_result.get_extra("system_notification"))
        result.set_extra("sms_notification", alert_result.get_extra("sms_notification"))
        result.set_extra("customer_phone", customer_phone)
        return result
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 Shelf & Warehouse Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_warehouse_stock(self) -> WarehouseStock:
        return self.__warehouse_stock

    def check_shelf_stock(self) -> list:
        """WarehouseStock ตรวจชั้นวางทั้งหมด + ส่ง Notification ถ้าของน้อย"""
        return self.__warehouse_stock.check_and_notify_low_stock()

    def refill_shelf_from_warehouse(self, staff_id: str, slot_id: str) -> dict:
        """Staff เติมสินค้าหลังได้รับแจ้งเตือน"""

        # 1. ค้นหา Staff
        staff = self.get_employee(staff_id)
        if not staff:
            return Result("error", f"ไม่พบพนักงานรหัส {staff_id}")
        if not isinstance(staff, Staff):
            return Result("error", f"พนักงาน {staff_id} ไม่ใช่ Staff (Barista/Rider เติมไม่ได้)")

        shelf_slot = self.__warehouse_stock.find_shelf_slot(slot_id)
        if not shelf_slot:
            return Result("error", f"ไม่พบชั้นวาง {slot_id}")
        

        # 3. Staff ดำเนินการเติม
        result_status = staff.refill_shelf(shelf_slot, self.__warehouse_stock)

        # 4. แปลผลลัพธ์
        product = shelf_slot.get_product()
        if result_status == "ALREADY_FULL":
            r = Result("info", f"ชั้นวาง {slot_id} ({product.get_name()}) เต็มแล้ว")
            r.set_extra("current_qty", shelf_slot.get_current_qty())
            r.set_extra("capacity", shelf_slot.get_capacity())
            return r
        elif result_status == "STATUS_FAILED":
            return Result("error", f"สินค้า {product.get_name()} ในคลังไม่เพียงพอ (เหลือ {product.get_qty()} ชิ้น)")
        elif result_status == "REFILL_COMPLETED":
            r = Result("success", f"เติม {product.get_name()} เข้าชั้นวาง {slot_id} สำเร็จ")
            r.set_extra("current_qty", shelf_slot.get_current_qty())
            r.set_extra("capacity", shelf_slot.get_capacity())
            r.set_extra("warehouse_remaining", product.get_qty())
            r.set_extra("staff_name", staff.get_name())
            return r
        
    # ✅ เพิ่มต่อท้ายใน class ShopController
    def start_barista_job(self, barista_id: str) -> dict:
        # หาบาริสต้า (ดึงผ่าน _ShopController__employees เพราะเพื่อนใช้ Private)
        barista = None
        for emp in self.__employees:
            if isinstance(emp, Barista) and emp.get_employee_id() == barista_id:
                barista = emp
                break
        if not barista:
            return Result("error", "ไม่พบพนักงาน Barista รหัสนี้")

        order_item = barista.get_slot().get_first_order()
        if not order_item:
            return Result("error", f"Barista {barista.get_name()} ไม่มีคิวชงน้ำ")

        product = order_item.get_product_order_item()
        drink_qty = order_item.get_qty()

        if not isinstance(product, CafeProduct):
            return Result("error", f"สินค้า {product.get_name()} ไม่มีสูตรชงน้ำ")

        recipe = product.get_recipe()
        is_enough = self.__warehouse_stock.check_ingredient(recipe, drink_qty)

        if not is_enough:
            return Result("error", f"วัตถุดิบในโกดังไม่พอชง {product.get_name()}!")

        barista.barista_make(recipe, self.__warehouse_stock, order_item)

        ingredient_detail = ""
        for ing in recipe.get_ingredients():
            per_cup = recipe.get_quantity_of_ingredient(ing)
            total_used = per_cup * drink_qty
            ingredient_detail += f"   - {ing.get_name()}: {per_cup} x {drink_qty} แก้ว = {total_used} หน่วย\n"

        r = Result("success")
        r.set_extra("product_name", product.get_name())
        r.set_extra("drink_qty", drink_qty)
        r.set_extra("barista_name", barista.get_name())
        r.set_extra("barista_id", barista.get_employee_id())
        r.set_extra("ingredient_detail", ingredient_detail)
        r.set_extra("remaining_queue", barista.check_queue_barista())
        return r





    
    
# ==========================================
# 2. Init MCP Server
# ==========================================
mcp = FastMCP("Shop_Bang_Korn_67_System")

# ==========================================
# 3. Database Mock
# ==========================================
shop_bang_korn_67 = ShopController()
# ✅ เปลี่ยนจาก add_barista / add_rider / add_staff → add_employee ทั้งหมด
shop_bang_korn_67.add_employee(Barista("EMP-001", "John (Barista 1)"))

rider1 = Rider("RD-001", "สมปอง ไวปานกามนิต", 30, "1กข 1234 กทม")
rider2 = Rider("RD-002", "สมชาย สายซิ่ง", 25, "9ฮฮ 9999 กทม")
shop_bang_korn_67.add_employee(rider1)
shop_bang_korn_67.add_employee(rider2)

staff1 = Staff("STF-001", "สมหญิง รักบริการ", 28, admin_level=1)
staff2 = Staff("STF-002", "สมชาย ใจเย็น", 35, admin_level=2)
shop_bang_korn_67.add_employee(staff1)
shop_bang_korn_67.add_employee(staff2)


coke = NormalProduct("DR-001", "Coke", 20, 100)
coffee = CafeProduct("CF-001", "Iced Latte", 65, 100)
beer = AlcoholProduct("ALC-001", "Beer", 60, 100, alcohol_percentage="5%")
lay = NormalProduct("GD-001", "Lay", 45, 100)
coffee_bean = IngredientProduct("ING-001", "เมล็ดกาแฟ", 0, 0)
milk = IngredientProduct("ING-002", "นมสด", 0, 0)
coffee.add_ingredient(coffee_bean, 2)  # Iced Latte ใช้กาแฟ 2 หน่วย
coffee.add_ingredient(milk, 1)         # ใช้นม 1 หน่วย


shop_bang_korn_67.add_product(coke)
shop_bang_korn_67.add_product(coffee)
shop_bang_korn_67.add_product(beer)
shop_bang_korn_67.add_product(lay)

shop_bang_korn_67.create_member(
    "0915919569", "คุณลูกค้า VIP",
    password="vip1234",
    address="99/9 KMITL ถ.ฉลองกรุง ลาดกระบัง กรุงเทพฯ 10520",
    distance_km=1.0
)
shop_bang_korn_67.create_member(
    "0912345678", "คุณสมชาย ใจดี",
    password="somchai1234",
    address="123/45 ซ.ลาดกระบัง 1 แขวงลาดกระบัง เขตลาดกระบัง กรุงเทพฯ 10520",
    distance_km=2.5
)
shop_bang_korn_67.create_member(
    "0898765432", "คุณสมหญิง รักดื่ม",
    password="somying1234",
    address="789 หมู่บ้านพฤกษา ถ.ฉลองกรุง ลาดกระบัง กรุงเทพฯ 10520",
    distance_km=5.0
)
# project.py — เพิ่มต่อจาก Mock Data เดิม (หลัง create_member)

# ==========================================
# 3.5 Mock Data — คลังสินค้า + ชั้นวาง
# ==========================================
warehouse = shop_bang_korn_67.get_warehouse_stock()

warehouse.add_ingredient_stock(coffee_bean, 200)
warehouse.add_ingredient_stock(milk, 100)

# ลงทะเบียนสินค้าเข้าคลัง
warehouse.add_product(coke)
warehouse.add_product(coffee)
warehouse.add_product(beer)
warehouse.add_product(lay)

# สร้างชั้นวาง (จำลองว่าบางชั้นของเหลือน้อย)
#                     slot_id       จุ   เหลือ  สินค้า   threshold
warehouse.add_shelf_slot(ShelfSlot("SHELF-001", 20,  3,  coke,    min_threshold=5))  # ⚠️ ต่ำกว่า!
warehouse.add_shelf_slot(ShelfSlot("SHELF-003", 10,  10, beer,    min_threshold=3))  # ✅ ปกติ
warehouse.add_shelf_slot(ShelfSlot("SHELF-004", 25,  1,  lay,     min_threshold=5))  # ⚠️ ต่ำกว่า

# ==========================================
# 4. MCP Tools
# ==========================================

# [แก้ไข] ปรับ description ให้ AI รู้ว่าต้องเรียก tool นี้ก่อน process_payment เสมอ
@mcp.tool()
def register_member(phone: str, name: str, password: str, age: int = 0,
                    address: str = "", distance_km: float = 0.0) -> str:
    """สมัครสมาชิกใหม่ในระบบร้านบางกอน67

    PREREQUISITE: ไม่มี (เรียกได้เลย)
    NEXT_STEP: เรียก login(phone, password) เพื่อเข้าสู่ระบบ

    Args:
        phone: เบอร์โทรศัพท์ (ห้ามซ้ำกับในระบบ)
        name: ชื่อสมาชิก
        password: รหัสผ่าน
        age: อายุ (default 0)
        address: ที่อยู่จัดส่ง (ถ้าไม่ใส่ สั่ง ONLINE ไม่ได้)
        distance_km: ระยะทางจากร้าน กม. (ใช้คำนวณค่าส่ง)

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมดที่ return มา ห้ามย่อ ห้ามสรุปเอง
    """
    if not phone or not password:
        return "Error: กรุณาระบุเบอร์โทรและรหัสผ่าน"

    result = shop_bang_korn_67.register_member(
        phone, name, password, age=age, address=address, distance_km=distance_km
    )
    if not result:
        return f"Error: เบอร์ {phone} ถูกใช้สมัครแล้ว"

    return (
        f"Success: สมัครสมาชิกสำเร็จ!\n"
        f"- ชื่อ: {name}\n"
        f"- เบอร์: {phone}\n"
        f"👉 กรุณาเรียก login เพื่อเข้าสู่ระบบ"
    )


@mcp.tool()
def login(phone: str = "", password: str = "") -> str:
    """เข้าสู่ระบบ — ต้องเรียกเป็นขั้นตอนแรกสุดก่อนสั่งซื้อ

    PREREQUISITE: ไม่มี (เรียกได้เลย)
    NEXT_STEP: เรียก add_product_to_basket() เพื่อเพิ่มสินค้าลงตะกร้า

    วิธีใช้:
    - Member login: ใส่ phone + password
    - Guest login: ไม่ต้องใส่อะไรเลย (phone="" password="")

    สิทธิ์:
    - Guest  → สั่งได้แค่ ONSITE เท่านั้น
    - Member → สั่งได้ทั้ง ONSITE + ONLINE

    บัญชีทดสอบ:
    - phone="0915919569" password="vip1234"     (คุณลูกค้า VIP, ระยะ 1.0 กม.)
    - phone="0912345678" password="somchai1234"  (คุณสมชาย ใจดี, ระยะ 2.5 กม.)
    - phone="0898765432" password="somying1234"  (คุณสมหญิง รักดื่ม, ระยะ 5.0 กม.)

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมดที่ return มา ห้ามย่อ ห้ามสรุปเอง
    """
    if shop_bang_korn_67.is_logged_in():
        return "Error: มีผู้ใช้ login อยู่แล้ว กรุณา logout ก่อน"
    
    # Guest login
    if not phone and not password:
        guest = shop_bang_korn_67.login_guest()
        return (
            f"Success: เข้าสู่ระบบแบบ Guest สำเร็จ\n"
            f"- สถานะ: ลูกค้าทั่วไป\n"
            f"- สิทธิ์: สั่งได้เฉพาะ ONSITE เท่านั้น\n"
            f"👉 เรียก add_product_to_basket เพื่อเริ่มสั่งซื้อ"
        )

    # Member login
    member = shop_bang_korn_67.login_member(phone, password)
    if not member:
        return "Error: เบอร์โทรหรือรหัสผ่านไม่ถูกต้อง"

    return (
        f"Success: เข้าสู่ระบบสำเร็จ!\n"
        f"- ชื่อ: {member.get_name()}\n"
        f"- เบอร์: {member.get_my_phone()}\n"
        f"- Tier: {member.get_tier().get_tier_name()}\n"
        f"- แต้มสะสม: {member.get_point()} แต้ม\n"
        f"- สิทธิ์: สั่งได้ทั้ง ONSITE + ONLINE\n"
        f"👉 เรียก add_product_to_basket เพื่อเริ่มสั่งซื้อ"
    )


@mcp.tool()
def logout() -> str:
    """ออกจากระบบ — ล้าง session ปัจจุบัน

    PREREQUISITE: ต้อง login อยู่
    NEXT_STEP: พร้อมเริ่มรอบใหม่ด้วย login()

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมด ห้ามย่อ
    """
    if not shop_bang_korn_67.is_logged_in():
        return "Error: ยังไม่มีผู้ใช้ login อยู่"

    session = shop_bang_korn_67.get_current_session()
    if isinstance(session, Member):
        name = session.get_name()
    else:
        name = "Guest"

    shop_bang_korn_67.logout()
    return f"Success: {name} ออกจากระบบเรียบร้อยแล้ว"

@mcp.tool()
def add_product_to_basket(product_id: str, qty: int, phone_member: str="") -> str:
    """ขั้นตอนที่ 1/3 — เพิ่มสินค้าลงตะกร้า

    PREREQUISITE: ต้องเรียก login() สำเร็จก่อน
    NEXT_STEP: เมื่อเพิ่มสินค้าครบแล้ว → เรียก process_payment()
    เรียกซ้ำได้หลายครั้งเพื่อเพิ่มสินค้าหลายรายการ

    รายการสินค้า:
    - "DR-001"  = Coke       20 บาท  (สินค้าปกติ)
    - "CF-001"  = Iced Latte 65 บาท  (เครื่องดื่มกาแฟ Barista ชง)
    - "ALC-001" = Beer       60 บาท  (แอลกอฮอล์ จำกัดเวลา+อายุ)
    - "GD-001"  = Lay        45 บาท  (สินค้าปกติ)

    Args:
        product_id: รหัสสินค้าจากรายการด้านบน
        qty: จำนวนชิ้น/แก้ว (ต้องมากกว่า 0)
        phone_member: ไม่ต้องใส่ ระบบดึงจาก session อัตโนมัติ

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมดที่ return มา ห้ามย่อ ห้ามสรุปเอง
    """
    # ===== บังคับ login ก่อน =====
    if not shop_bang_korn_67.is_logged_in():
        return "Error: กรุณา login ก่อน (เรียก tool 'login')"


    session = shop_bang_korn_67.get_current_session()
    # ถ้าใส่ phone_member มา → ต้องตรงกับ session ที่ login อยู่
    if phone_member and phone_member.strip() != "":
        if not isinstance(session, Member):
            return "Error: Login อยู่แบบ Guest แต่ใส่เบอร์สมาชิก — กรุณา logout แล้ว login ด้วยเบอร์สมาชิก"
        if session.get_my_phone() != phone_member.strip():
            return f"Error: เบอร์ {phone_member} ไม่ตรงกับ session ที่ login อยู่ ({session.get_my_phone()})"
        
    
    customer_obj = session  # ✅ ใช้ session เสมอ (ทั้ง Member และ Guest)

    basket = customer_obj.get_basket()

    selected_product = shop_bang_korn_67.get_product_by_id(product_id)
    if not selected_product:
        return f"Error: ไม่พบสินค้าหมายเลข {product_id} ในร้าน"

    is_alcohol = selected_product.validate_alcohol()
    if is_alcohol:
        if not selected_product.validate_sale_time(datetime.now()):
            return "Error: นอกเวลาขายแอลกอฮอล์ (ขายได้เฉพาะ 11:00-14:00 และ 17:00-24:00)"
        if customer_obj.get_age() < selected_product.get_restricted_age():
            return "Error: ลูกค้าอายุไม่ถึง 20 ปี ไม่สามารถซื้อแอลกอฮอล์ได้"

    if not selected_product.is_available(qty):
        return "Error: สินค้ามีไม่เพียงพอ หรือหมดสต็อก"

    new_order_item = basket.create_order_item(selected_product, qty)
    success = basket.add_to_basket(new_order_item)

    if success:
        count = sum(item.get_qty() for item in basket.get_basket_items())
        if isinstance(customer_obj, Member):
            customer_label = f"สมาชิก {customer_obj.get_name()}"
        else:
            customer_label = "ลูกค้าทั่วไป (Guest)"
        return (
            f"Success: เพิ่ม {selected_product.get_name()} จำนวน {qty} ชิ้น "
            f"ลงตะกร้าของ{customer_label} เรียบร้อย "
            f"(รวมในตะกร้า {count} ชิ้น)\n"
            f"👉 พร้อมชำระเงินได้โดยเรียก process_payment"
        )

@mcp.tool()
def process_payment(payment_channel: str, received_amount: float = 0.0,phone_number: str="", 
                    order_type: str = "ONSITE") -> str:
    """ขั้นตอนที่ 2/3 — สร้าง Order + ชำระเงิน

    PREREQUISITE: ต้องเรียก login() + add_product_to_basket() สำเร็จก่อน
    NEXT_STEP (ดูจากผลลัพธ์ที่ return):
    - ถ้ามี Barista รับคิว → เรียก process_barista_order() ก่อน
    - ถ้า ONSITE (ไม่มีเครื่องดื่ม) → เรียก create_transaction() ออกใบเสร็จ
    - ถ้า ONLINE → เรียก rider_accept_order() ให้ Rider รับงาน

    Args:
        payment_channel: "CASH" / "QR" / "COD"
            - CASH: ต้องใส่ received_amount ด้วย
            - QR: ไม่ต้องใส่ received_amount
            - COD: ใช้ได้เฉพาะ ONLINE (ONSITE ใช้ COD ไม่ได้)
        received_amount: จำนวนเงินที่รับมา (เฉพาะ CASH ถ้าไม่พอจะ error)
        phone_number: ไม่ต้องใส่ ระบบดึงจาก session
        order_type: "ONSITE" (ซื้อหน้าร้าน) หรือ "ONLINE" (สั่งส่ง เฉพาะ Member)

    กฎ:
    - Guest สั่ง ONLINE ไม่ได้
    - ONSITE + COD ไม่ได้
    - เครื่องดื่มสั่งได้สูงสุด 10 แก้วต่อออเดอร์

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมด ห้ามย่อ ห้ามตัด ORDER ID ออก
                 ต้องจดจำ ORDER ID ไว้ใช้ในขั้นตอนถัดไป
    """
    # ===== บังคับ login =====
    if not shop_bang_korn_67.is_logged_in():
        return "Error: กรุณา login ก่อน (เรียก tool 'login')"

    session = shop_bang_korn_67.get_current_session()

    if phone_number and phone_number.strip() != "":
        if not isinstance(session, Member):
            return "Error: Login อยู่แบบ Guest แต่ใส่เบอร์สมาชิก"
        if session.get_my_phone() != phone_number.strip():
            return f"Error: เบอร์ {phone_number} ไม่ตรงกับ session ที่ login อยู่ ({session.get_my_phone()})"

    customer_obj = session  # ✅ ใช้ session เสมอ

    # ===== บังคับ: Guest สั่ง ONLINE ไม่ได้ =====
    if order_type.upper() == "ONLINE" and not isinstance(customer_obj, Member):
        return "Error: Guest สั่งแบบ ONLINE ไม่ได้ — กรุณา login ด้วยเบอร์สมาชิก หรือสั่งแบบ ONSITE"

    # ===== เงื่อนไขเดิมทั้งหมด (คงไว้) =====
    if order_type.upper() == "ONLINE":
        if not customer_obj.get_address():
            return "Error: สมาชิกยังไม่ได้ตั้งค่าที่อยู่จัดส่ง"
        if not shop_bang_korn_67.get_available_rider():
            return "Error: ไม่มี Rider ว่าง"

    if order_type.upper() == "ONSITE" and payment_channel.upper() == "COD":
        return "Error: ONSITE ไม่สามารถชำระเงินปลายทาง (COD) ได้"

    basket = customer_obj.get_basket()
    items = basket.get_basket_items()

    if not items:
        return "Error: ตะกร้าว่าง — กรุณาเรียก add_product_to_basket ก่อน"

    for item in items:
        product = item.get_product_order_item()
        if product.validate_alcohol():
            if not product.validate_sale_time(datetime.now()):
                return "Error: มีแอลกอฮอล์ในตะกร้า นอกเวลาขาย"

    drink_count = basket.count_drink_items()
    if drink_count > 10:
        return "Error: สั่งเครื่องดื่มได้สูงสุด 10 แก้ว"

    assigned_barista = None
    if drink_count > 0:
        baristas = shop_bang_korn_67.get_employee(role=Barista)
        for barista in baristas:
            if barista.can_accept_order(drink_count):
                assigned_barista = barista
                break
        if not assigned_barista:
            return "Error: คิวบาริสต้าเต็ม"

    new_order = shop_bang_korn_67.create_order(customer_obj, order_type.upper())
    total_price = new_order.calculate_total()

    # ===== ชำระเงิน (เหมือนเดิม) =====
    if payment_channel.upper() == "QR":
        channel = QRPayment()
        payment = shop_bang_korn_67.create_payment(new_order, channel, total_price)
        new_order.set_payment(payment)
        qr_data = channel.generate_qr_code(total_price)
        payment.set_status("Success")
        payment_msg = f"สร้าง QR Code สำเร็จ (QR Data: {qr_data})"

    elif payment_channel.upper() == "CASH":
        channel = CashPayment(received_amount)
        payment = shop_bang_korn_67.create_payment(new_order, channel, total_price)
        new_order.set_payment(payment)
        try:
            change = channel.calculate_change(total_price)
            payment.set_status("Success")
            payment_msg = f"รับเงินสด {received_amount} บาท | เงินทอน {change} บาท"
        except ValueError as e:
            payment.set_status("Failed")
            return f"Error: {str(e)} (ยอด {total_price} บาท แต่รับมา {received_amount} บาท)"

    elif payment_channel.upper() == "COD":
        channel = CODPayment()
        payment = shop_bang_korn_67.create_payment(new_order, channel, total_price)
        new_order.set_payment(payment)
        payment.set_status("Pending (COD)")
        payment_msg = f"ชำระเงินปลายทาง (COD) ยอด {total_price} บาท"
    else:
        return "Error: ช่องทางไม่ถูกต้อง (QR, CASH, COD)"

    if payment.is_paid() or payment.get_status() == "Pending (COD)":
        if assigned_barista:
            assigned_barista.assign_drinks(items)
            new_order.set_assigned_barista(assigned_barista)
            # 🆕 เพิ่มข้อความแนะนำ
            result_msg_barista = (
                f"\n- ☕ Barista: {assigned_barista.get_name()} "
                f"รับคิวชง {drink_count} แก้ว"
            )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🔄 แก้ไข: แยกการหักสต็อกตามประเภท Order
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        warehouse = shop_bang_korn_67.get_warehouse_stock()

        for item in items:
            product = item.get_product_order_item()
            qty = item.get_qty()
            pid = product.get_product_id()

            if order_type.upper() == "ONSITE":
                # ONSITE: หักจากชั้นวาง (ShelfSlot)
                # ลูกค้ามาซื้อหน้าร้าน → หยิบของจากชั้น
                
                shelf_success = warehouse.deduct_from_shelf(pid, qty)
                if shelf_success:
                    new_order.set_stock_source(pid, "shelf")       # 🆕 บันทึก
                else:
                    # ถ้าชั้นไม่มี/ไม่พอ → fallback หักจากคลังตรง
                    product.deduct_stock(qty)
                    new_order.set_stock_source(pid, "warehouse")   # 🆕 บันทึก

            else:
                # ONLINE: หักจากคลัง (Product.stock_qty)
                # จัดส่ง → เตรียมของจากคลังแพ็คส่ง
                product.deduct_stock(qty)
                new_order.set_stock_source(pid, "warehouse")       # 🆕 บันทึก

        shop_bang_korn_67.add_order(new_order)

        result_msg = (
            f"✅ สร้างออเดอร์สำเร็จ!\n"
            f"═══════════════════════════════════════\n"
            f"📦 Order ID : {new_order.get_order_id()}\n"
            f"💰 ยอดรวม   : {total_price:.2f} บาท\n"
            f"💳 ชำระผ่าน : {payment_msg}\n"
            f"═══════════════════════════════════════\n"
        )

        if order_type.upper() == "ONLINE" and isinstance(customer_obj, Member):
            new_order.update_status("Waiting for Rider")
            result_msg += (
                f"📍 ประเภท   : ONLINE (จัดส่ง)\n"
                f"🏠 ที่อยู่    : {customer_obj.get_address()}\n"
                f"📏 ระยะทาง  : {customer_obj.get_distance_km()} กม.\n"
                f"🚚 ค่าจัดส่ง : {new_order.get_delivery_fee():.2f} บาท\n"
            )
            next_step_msg = "\n👉 ขั้นตอนถัดไป: เรียก rider_accept_order เพื่อให้ Rider มารับงาน"
        else:
            new_order.update_status("Paid")
            result_msg += f"📍 ประเภท   : ONSITE (ซื้อหน้าร้าน)\n"
            next_step_msg = "\n👉 ขั้นตอนถัดไป: เรียก create_transaction เพื่อออกใบเสร็จ"

        if isinstance(customer_obj, Member):
            earned_points = new_order.calculate_member_point()
            customer_obj.received_point(earned_points)
            customer_obj.clear_basket()
            result_msg += (
                f"═══════════════════════════════════════\n"
                f"👤 สมาชิก  : {customer_obj.get_name()}\n"
                f"📞 เบอร์    : {customer_obj.get_my_phone()}\n"
                f"🏅 Tier    : {customer_obj.get_tier().get_tier_name()}\n"
                f"⭐ ได้แต้ม  : +{earned_points} แต้ม (รวม {customer_obj.get_point()} แต้ม)\n"
            )
        else:
            customer_obj.clear_basket()
            result_msg += (
                f"═══════════════════════════════════════\n"
                f"👤 สถานะ   : ลูกค้าทั่วไป (Guest)\n"
            )

        result_msg += f"═══════════════════════════════════════\n"
        result_msg += f"\n*** ORDER ID: {new_order.get_order_id()} ***"

        if assigned_barista:
            result_msg += (
                f"\n\n☕ เครื่องดื่ม {drink_count} แก้ว → คิว Barista: {assigned_barista.get_name()}"
                f"\n👉 เรียก process_barista_order('{assigned_barista.get_employee_id()}') เพื่อให้ Barista เริ่มชง"
            )

        result_msg += next_step_msg
        return result_msg
    else:
        return "Error: การชำระเงินล้มเหลว"

@mcp.tool()
def process_barista_order(barista_id: str) -> str:
    """สั่งให้ Barista ชงเครื่องดื่มคิวถัดไป (ชงทีละ 1 OrderItem)

    PREREQUISITE: ต้องเรียก process_payment() สำเร็จก่อน
                  และผลลัพธ์ต้องแสดงว่ามี Barista รับคิว
    NEXT_STEP:
    - ถ้า Barista ยังมีคิวเหลือ → เรียก process_barista_order() อีกครั้ง
    - ถ้าคิวหมดแล้ว + ONSITE → เรียก create_transaction()
    - ถ้าคิวหมดแล้ว + ONLINE → เรียก rider_accept_order()

    การทำงาน:
    1. ดึงเครื่องดื่มคิวแรกจาก BaristaSlot
    2. ตรวจวัตถุดิบในคลัง (คูณจำนวนแก้ว)
    3. ตัดสต็อกวัตถุดิบจากคลัง
    4. อัปเดตสถานะ Queued → Preparing → Ready
    5. เคลียร์ออกจากคิว Barista

    Args:
        barista_id: รหัส Barista เช่น "EMP-001" = John (Barista 1)

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมด ห้ามย่อ
    """
    result = shop_bang_korn_67.start_barista_job(barista_id)

    if result.get_status() == "error":
        return f"❌ Error: {result.get_message()}"

    remaining = result.get_extra("remaining_queue")
    response = (
        f"☕ ชงเครื่องดื่มสำเร็จ!\n"
        f"═══════════════════════════════════════\n"
        f"🥤 เครื่องดื่ม : {result.get_extra('product_name')} x{result.get_extra('drink_qty')} แก้ว\n"
        f"👨‍🍳 ชงโดย     : {result.get_extra('barista_name')} ({result.get_extra('barista_id')})\n"
        f"📊 สถานะ     : Queued → Preparing → Ready ✅\n"
        f"═══════════════════════════════════════\n"
        f"🏭 วัตถุดิบที่ใช้:\n"
        f"{result.get_extra('ingredient_detail')}"
        f"═══════════════════════════════════════\n"
    )

    if remaining > 0:
        response += (
            f"⏳ เหลือคิวอีก {remaining} แก้ว\n"
            f"👉 เรียก process_barista_order('{result.get_extra('barista_id')}') อีกครั้งเพื่อชงแก้วถัดไป"
        )
    else:
        response += (
            f"✅ คิวเครื่องดื่มหมดแล้ว! พร้อมดำเนินการขั้นตอนถัดไป\n"
            f"👉 ONSITE → เรียก create_transaction()\n"
            f"👉 ONLINE → เรียก rider_accept_order()"
        )

    return response

@mcp.tool()
def rider_accept_order(rider_id: str) -> str:
    """Rider รับงานส่งของ — เฉพาะ ONLINE Order ที่รอ Rider อยู่

    PREREQUISITE: ต้องเรียก process_payment(order_type="ONLINE") สำเร็จก่อน
                  ถ้ามีเครื่องดื่มต้อง process_barista_order() ก่อนด้วย
    NEXT_STEP: เรียก rider_confirm_delivery(rider_id) เมื่อส่งถึงลูกค้า

    การทำงาน:
    - ค้นหา Order ที่รอ Rider อัตโนมัติ (FIFO) ไม่ต้องระบุ order_id
    - Assign Rider + เปลี่ยนสถานะเป็น Delivering
    - ถ้า COD จะแจ้งว่าต้องเก็บเงินตอนส่งถึง

    Args:
        rider_id: รหัส Rider
            - "RD-001" = สมปอง ไวปานกามนิต (ทะเบียน 1กข 1234 กทม)
            - "RD-002" = สมชาย สายซิ่ง (ทะเบียน 9ฮฮ 9999 กทม)

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมด ห้ามย่อ
    """

    rider = shop_bang_korn_67.get_employee(rider_id)
    if not isinstance(rider, Rider):
        return f"Error: พนักงานรหัส {rider_id} ไม่ใช่ Rider หรือไม่พบในระบบ"
    
    if not rider.is_available():
        return f"Error: Rider {rider.get_name()} กำลังติดงานอื่นอยู่ ไม่ว่างรับงานใหม่"

    # 3. ✅ ค้นหาออเดอร์ที่รอ Rider อัตโนมัติ (ไม่ต้องรับ order_id จากผู้ใช้)
    pending_orders = shop_bang_korn_67.get_pending_delivery_orders()

    if not pending_orders:
        return "ℹ️ ไม่มีออเดอร์ที่รอ Rider รับงานในขณะนี้"

    # 4. เลือกออเดอร์แรกที่เข้าคิว (FIFO - First In First Out)
    order = pending_orders[0]
    order_id = order.get_order_id()

    # Assign Rider และเปลี่ยนสถานะรถเป็นไม่ว่าง
    order.assign_rider(rider)
    rider.set_available(False)
    
    # 🚨 [เพิ่มใหม่] อัปเดตสถานะออเดอร์ว่ากำลังไปส่ง
    order.update_status("Delivering")

    # 7. กรณี COD → สมมติว่า Rider เก็บเงินสำเร็จ
    result_msg = (
        f"✅ จับคู่ Rider กับ Order สำเร็จ!\n"
        f"═══════════════════════════════════════\n"
        f"📦 ออเดอร์   : {order_id}\n"
        f"🏍️ Rider     : {rider.get_name()}\n"
        f"🪪 รหัส      : {rider.get_employee_id()}\n"
        f"🔢 ทะเบียน   : {rider.get_license_plate()}\n"
        f"📍 สถานะ     : Delivering (กำลังจัดส่ง)\n"
        f"═══════════════════════════════════════"
    )

    order_payment = order.get_payment()
    if order_payment and order_payment.get_payment_channel().get_channel_type() == "COD":
        result_msg += (
            f"\n💵 การชำระเงิน: COD (เก็บเงินปลายทาง)\n"
            f"   ยอดที่ต้องเก็บ: {order_payment.get_amount():.2f} บาท\n"
            f"   ⚠️ เก็บเงินเมื่อส่งถึงลูกค้าเท่านั้น"
        )

    remaining = len(pending_orders) - 1
    if remaining > 0:
        result_msg += f"\n\n⏳ ยังมีออเดอร์รอ Rider อีก {remaining} รายการ"

    result_msg += f"\n\n👉 เมื่อส่งถึงลูกค้าแล้ว → เรียก rider_confirm_delivery('{rider.get_employee_id()}')"
    return result_msg

@mcp.tool()
def rider_confirm_delivery(rider_id: str) -> str:
    """Rider ยืนยันส่งถึงลูกค้าแล้ว + เก็บเงิน COD (ถ้ามี)

    PREREQUISITE: ต้องเรียก rider_accept_order() สำเร็จก่อน (Order status=Delivering)
    NEXT_STEP: เรียก create_transaction() เพื่อออกใบเสร็จ

    Args:
        rider_id: รหัส Rider ที่กำลังส่งของอยู่ (ตัวเดียวกับ rider_accept_order)

    OUTPUT_RULE: แสดงผลลัพธ์ทั้งหมด ห้ามย่อ
    """
    rider = shop_bang_korn_67.get_employee(rider_id)
    if not rider or not isinstance(rider, Rider):
        return f"Error: ไม่พบ Rider ID: {rider_id}"

    # ค้นหา Order ที่ Rider กำลังส่ง (status = "Delivering")
    order = shop_bang_korn_67.find_order_by_rider(rider_id)
    if not order:
        return f"Error: Rider {rider.get_name()} ไม่มี Order ที่กำลังส่งอยู่"

    # ===== เก็บเงิน COD ณ จุดส่งถึง =====
    cod_msg = ""
    order_payment = order.get_payment()
    if order_payment and order_payment.get_payment_channel().get_channel_type() == "COD":
        if not order_payment.is_paid():
            order_payment.make_payment(order_payment.get_amount())
            cod_msg = f"\n   💵 เก็บเงินปลายทาง (COD) สำเร็จ: {order_payment.get_amount():.2f} บาท"

    # ===== อัปเดตสถานะ =====
    order.update_status("Delivered")
    rider.set_available(True)  # Rider ว่างแล้ว พร้อมรับงานใหม่

    return (
        f"✅ ยืนยันส่งสินค้าถึงลูกค้าเรียบร้อย!\n"
        f"═══════════════════════════════════════\n"
        f"📦 Order     : {order.get_order_id()}\n"
        f"🏍️ Rider     : {rider.get_name()} ({rider.get_license_plate()})\n"
        f"📍 สถานะ     : Delivered (ส่งถึงลูกค้าแล้ว)\n"
        f"🏍️ Rider     : กลับมาว่าง พร้อมรับงานใหม่{cod_msg}\n"
        f"═══════════════════════════════════════\n"
        f"\n👉 ขั้นตอนถัดไป: เรียก create_transaction เพื่อออกใบเสร็จ"
    )


@mcp.tool()
def create_transaction(staff_id: str, order_id: str) -> str:
    """ขั้นตอนที่ 3/3 สุดท้าย — ออกใบเสร็จ Transaction

    PREREQUISITE:
    - ONSITE: login → add_product_to_basket → process_payment → (process_barista_order) → create_transaction
    - ONLINE: login → add_product_to_basket → process_payment → (process_barista_order) → rider_accept_order → rider_confirm_delivery → create_transaction
    NEXT_STEP: Flow จบ เรียก logout() หรือเริ่มรอบใหม่ได้

    Args:
        staff_id: รหัส Staff (ต้องเป็น Staff เท่านั้น Barista/Rider ใช้ไม่ได้)
            - "STF-001" = สมหญิง รักบริการ (Cashier, admin_level=1)
            - "STF-002" = สมชาย ใจเย็น (Manager, admin_level=2)
        order_id: รหัส Order ที่ได้จาก process_payment (ห้ามแต่งเอง ต้องใช้ค่าจริง)

    OUTPUT_RULE: ข้อความที่ return คือใบเสร็จฉบับเต็ม
                 ต้องแสดงทุกบรรทัดเป๊ะๆ ห้ามตัดทอน ห้ามสรุป ห้ามย่อ ห้ามดัดแปลง
                 รวมถึง TRANSACTION ID ต้องแสดงด้วย
    """
    try:
        # 1. ค้นหาพนักงานจากฐานข้อมูลรวม
        emp = shop_bang_korn_67.get_employee(staff_id)
        if not emp:
            return f"Error: ไม่พบพนักงานรหัส {staff_id} ในระบบ"

        # 2. ตรวจสอบสิทธิ์ (ต้องเป็น Staff เท่านั้น Barista/Rider ออกใบเสร็จไม่ได้)
        # ถ้าอยากเช็คแอดมิน (เช่น เลเวล >= 2 ค่อยให้ทำ) ก็เพิ่ม emp.get_admin_level() เข้าไปตรงนี้ได้เลย
        if not isinstance(emp, Staff):
            return f"Error: Unauthorized! พนักงานรหัส {staff_id} ไม่มีสิทธิ์ในการออกใบเสร็จ"

        # 3. Fetch Order
        order = shop_bang_korn_67.get_order_by_id(order_id)
        if not order:
            return "Error: Order Not Found (ไม่พบออเดอร์ หรือยังไม่ได้ทำ process_payment)"

        # 🚨 [เพิ่มใหม่] ล็อกการส่งมอบ: ถ้าเป็น Online Order ต้องมี Rider มารับงานแล้วเท่านั้น ไม่งั้นส่งของไม่ได้
        # ──── หลังแก้ (ใหม่) ────
        if isinstance(order, OnlineOrder):
            if order.get_status() != "Delivered":
                current_status = order.get_status()
                if current_status == "Waiting for Rider":
                    return f"Error: ออเดอร์ {order_id} ยังไม่มี Rider มารับงาน → เรียก rider_accept_order ก่อน"
                elif current_status == "Delivering":
                    return f"Error: ออเดอร์ {order_id} กำลังจัดส่ง ยังไม่ถึงลูกค้า → เรียก rider_confirm_delivery ก่อน"
                else:
                    return f"Error: ออเดอร์ {order_id} สถานะไม่ถูกต้อง ({current_status})"
        # ✅ หลังแก้ — เช็คสถานะจาก Payment object ที่ผูกกับ Order
        # 4. Check Payment Status
        order_payment = order.get_payment()
        if not order_payment or not order_payment.is_paid():
            return "Error: Payment Incomplete (ออเดอร์นี้ยังไม่ผ่านการชำระเงิน หรือยังเก็บเงิน COD ไม่สำเร็จ)"
        
        # 5. Create Transaction
        payment_channel = order_payment.get_payment_channel().get_channel_type()
        transaction = Transaction(emp, order, payment_channel) # ใช้ emp ที่ผ่านการเช็คสิทธิ์แล้ว
        if order.get_order_type().upper() == "ONSITE":
            order.update_status("Completed")
        elif order.get_order_type().upper() == "ONLINE":
            order.update_status("Delivered & Completed")

        # ✅ บันทึก Transaction ลงระบบ เพื่อให้ void_transaction ค้นหาได้
        shop_bang_korn_67.add_transaction(transaction)
        # ✅ เพิ่มตรงนี้
        customer = order.get_customer()
        if isinstance(customer, Member):
            customer.add_transaction_history(transaction)
       
        receipt = transaction.generate_receipt()

        result_msg = (
            f"✅ ออกใบเสร็จสำเร็จ!\n"
            f"═══════════════════════════════════════\n\n"
            f"{receipt}\n"
            f"*** TRANSACTION ID: {transaction.get_transaction_id()} ***\n"
            f"\n💡 หากต้องการยกเลิกรายการนี้ภายหลัง\n"
            f"   → ใช้ void_transaction โดย Staff ที่มี admin_level >= 2\n"
            f"   → Transaction ID: {transaction.get_transaction_id()}"
        )
        return result_msg
    except Exception as e:
        return f"Error: {str(e)}"
    
# project.py — เพิ่มต่อจาก @mcp.tool() def create_transaction

@mcp.tool()
def void_transaction(staff_id: str, transaction_id: str, void_reason: str) -> str:
    """Void (ยกเลิก) Transaction ที่ออกใบเสร็จแล้ว — tool อิสระ

    PREREQUISITE: ต้องมี Transaction ที่สร้างจาก create_transaction() ก่อน
    ห้ามเรียกเอง ต้องรอผู้ใช้ร้องขอยกเลิกเท่านั้น

    Args:
        staff_id: ต้องเป็น Staff ที่มี admin_level >= 2 เท่านั้น
            - "STF-001" (admin_level=1) → ไม่มีสิทธิ์ Void
            - "STF-002" (admin_level=2) → มีสิทธิ์ Void
        transaction_id: UUID ที่ได้จาก create_transaction (ห้ามแต่งเอง)
        void_reason: เหตุผลการยกเลิก เช่น "ลูกค้าเปลี่ยนใจ"

    การทำงาน:
    - ตรวจสิทธิ์ Staff (admin_level >= 2)
    - ป้องกัน Void ซ้ำ
    - คืนเงิน + คืนสต็อก + หักแต้มสมาชิก + ปลดคิว Barista

    OUTPUT_RULE: แสดง Void Receipt ทั้งหมด ห้ามย่อ ห้ามสรุป
    """
    try:
        # ===== 1. SC->>SC: get_employee(staff_id) =====
        staff = shop_bang_korn_67.get_employee(staff_id)
        if not staff:
            return f"Error: ไม่พบพนักงานรหัส {staff_id} ในระบบ"

        # ===== 2. ตรวจว่าเป็น Staff class จริงไหม =====
        if not isinstance(staff, Staff):
            return f"Error: พนักงานรหัส {staff_id} ไม่ใช่ Staff (อาจเป็น Barista/Rider) จึงไม่มีสิทธิ์ Void"

        # ===== 3. SC->>S: validate_admin() =====
        if not staff.validate_admin():
            return (
                f"Error: Unauthorized! พนักงาน {staff.get_name()} ({staff_id}) "
                f"มี admin_level={staff.get_admin_level()} ซึ่งไม่เพียงพอ "
                f"(ต้องการ admin_level >= 2 เพื่อทำการ Void)"
            )

        # ===== 4. SC->>SC: get_transaction_by_id(transaction_id) =====
        transaction = shop_bang_korn_67.get_transaction_by_id(transaction_id)
        if not transaction:
            return f"Error: ไม่พบ Transaction ID: {transaction_id} ในระบบ (อาจพิมพ์ผิด หรือยังไม่ได้เรียก create_transaction)"

        # ===== 5. ตรวจสถานะ — ป้องกัน Void ซ้ำ =====
        if transaction.get_status() == "Voided":
            return f"Error: Transaction {transaction_id} ถูก Void ไปแล้วก่อนหน้านี้ ไม่สามารถ Void ซ้ำได้"

        # ===== 6. SC->>SC: create_voidtransaction(...) =====
        void_record = shop_bang_korn_67.create_voidtransaction(transaction, void_reason, staff)
        shop_bang_korn_67.add_transaction(void_record)  # บันทึก VoidTransaction ลงระบบ

        # ===== 7. SC->>T: update_status("Voided") =====
        transaction.update_status("Voided")

        # ===== 8. SC->>T: void_related_order() → Order.process_refund() =====
        transaction.void_related_order()

        # ===== 9. SC->>T: restock_related_order() → Product.restock_product() =====
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🆕 เพิ่มใหม่: ถ้า ONSITE → คืนของเข้าชั้นวางด้วย
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # ===== 9. คืนสต็อก — แยกตามประเภท =====
                # ===== 9. คืนสต็อก — ดูจาก stock_source ที่บันทึกไว้ =====
        order = transaction.get_order()
        customer = order.get_customer()

        warehouse = shop_bang_korn_67.get_warehouse_stock()
        basket_items = order.get_basket().get_basket_items()

        for item in basket_items:
            product = item.get_product_order_item()
            qty = item.get_qty()
            pid = product.get_product_id()

            source = order.get_stock_source(pid)

            if source == "shelf":
                # ตอนขายหักจาก shelf → คืนเข้า shelf
                warehouse.restock_to_shelf(pid, qty)
            else:
                # ตอนขายหักจาก warehouse → คืนเข้า warehouse
                product.restock_product(qty)


        if isinstance(customer, Member):
            earned_points = order.calculate_member_point()
            # ต้องเพิ่ม method deduct_points ใน Member class
            customer.deduct_points(earned_points)

        barista = order.get_assigned_barista()
        if barista:
            basket_items = order.get_basket().get_basket_items()
            barista.remove_drinks(basket_items)
        # ===== 10. สร้าง Void Receipt =====
        void_receipt = void_record.generate_void_receipt()
        refund_amount = order.get_payment().get_amount()

        result_msg = (
            f"✅ ยกเลิกรายการสำเร็จ!\n"
            f"═══════════════════════════════════════\n\n"
            f"{void_receipt}\n"
            f"📋 สรุปการดำเนินการ:\n"
            f"═══════════════════════════════════════\n"
            f"👤 ลูกค้า           : {customer.get_name()}\n"
            f"💰 เงินที่คืน        : {refund_amount:.2f} บาท\n"
            f"📦 สินค้าคืน Stock  : ✅ เรียบร้อย\n"
        )

        if isinstance(customer, Member):
            result_msg += f"⭐ หักแต้มคืน       : ✅ {order.calculate_member_point()} แต้ม\n"

        if barista:
            result_msg += f"☕ ปลดคิว Barista  : ✅ เรียบร้อย\n"

        result_msg += (
            f"👨‍💼 Void โดย        : {staff.get_name()} ({staff_id})\n"
            f"📋 เหตุผล          : {void_reason}\n"
            f"═══════════════════════════════════════"
        )
        return result_msg

    except Exception as e:
        return f"Error: เกิดข้อผิดพลาดในการ Void — {str(e)}"
    
@mcp.tool()
def get_member_history(phone_number: str) -> str:
    """ดูประวัติ Transaction ทั้งหมดของสมาชิก — tool อิสระ เรียกได้ตลอด

    Args:
        phone_number: เบอร์โทรสมาชิก เช่น "0915919569"

    OUTPUT_RULE: แสดงผลทั้งหมด ห้ามย่อ
    """
    member = shop_bang_korn_67.get_member(phone_number)
    if not member:
        return f"Error: ไม่พบสมาชิกเบอร์ {phone_number}"

    history = member.get_transaction_history()
    if not history:
        return f"สมาชิก {member.get_name()} ยังไม่มีประวัติ Transaction"

    result = f"ประวัติของ {member.get_name()} ({phone_number}):\n"
    for i, txn in enumerate(history, 1):
        result += (
            f"  {i}. Transaction: {txn.get_transaction_id()}\n"
            f"     Order: {txn.get_order().get_order_id()}\n"
            f"     Status: {txn.get_status()}\n"
        )
    result += f"\nรวม {len(history)} รายการ"
    return result


@mcp.tool()
def rider_report_emergency(rider_id: str, reason: str) -> str:
    """Rider แจ้งเหตุฉุกเฉินระหว่างจัดส่ง — tool อิสระ

    PREREQUISITE: ต้องมี Order ที่ Rider กำลังส่งอยู่ (status=Delivering)
    NEXT_STEP:
    - เรียก rider_accept_order(rider_id_ใหม่) เพื่อให้ Rider คนใหม่รับงาน
    - หรือเรียก rider_clear_emergency(rider_id) เพื่อคืนสถานะ Rider เดิม

    การทำงาน:
    - แจ้ง Staff อัตโนมัติ (ส่ง SystemNotification)
    - ส่ง SMS แจ้งลูกค้า (ถ้าเป็น Member)
    - ปลด Rider เดิมออกจาก Order
    - Order กลับไปสถานะ Waiting for Rider

    Args:
        rider_id: รหัส Rider ที่แจ้งเหตุ
            - "RD-001" = สมปอง ไวปานกามนิต
            - "RD-002" = สมชาย สายซิ่ง
        reason: เหตุผล เช่น "รถเสีย" "อุบัติเหตุ" "ฝนตกหนัก"

    OUTPUT_RULE: แสดงผลทั้งหมด ห้ามย่อ รวมถึงสถานะ Notification
    """
    try:
        result = shop_bang_korn_67.report_emergency(rider_id, reason)

        if result.get_status() == "error":
            return f"Error: {result.get_message()}"

        noti_lines = ""

        if result.get_extra("system_notification") == "success":
            noti_lines += f"   🖥️ แจ้งระบบ (Staff/Admin): ส่งสำเร็จ ✅\n"
        else:
            noti_lines += f"   🖥️ แจ้งระบบ (Staff/Admin): ล้มเหลว ❌\n"

        if result.get_extra("sms_notification") == "success":
            noti_lines += f"   📱 SMS ถึงลูกค้า ({result.get_extra('customer_phone')}): ส่งสำเร็จ ✅\n"
        elif result.get_extra("sms_notification") == "no_phone":
            noti_lines += f"   📱 SMS ถึงลูกค้า: ไม่มีเบอร์โทร (Guest) ⚠️\n"
        else:
            noti_lines += f"   📱 SMS ถึงลูกค้า: ล้มเหลว ❌\n"

        response = (
            f"🚨 แจ้งเหตุฉุกเฉินสำเร็จ!\n"
            f"═══════════════════════════════════════\n"
            f"   📦 Order: {result.get_extra('order_id')}\n"
            f"   🏍️ Rider เดิม: {result.get_extra('rider_released')}\n"
            f"   📋 เหตุผล: {result.get_extra('reason')}\n"
            f"   👨‍💼 Staff รับเรื่อง: {result.get_extra('handled_by')}\n"
            f"   📍 สถานะ Order: {result.get_extra('new_order_status')}\n"
            f"═══════════════════════════════════════\n"
            f"\n"
            f"📨 สถานะการแจ้งเตือน:\n"
            f"{noti_lines}"
            f"\n"
            f"✅ ดำเนินการแล้ว:\n"
            f"   - ปลด Rider เดิมออกจาก Order แล้ว\n"
            f"   - Order กลับไปรอ Rider คนใหม่\n"
            f"\n"
            f"👉 เรียก rider_accept_order เพื่อให้ Rider คนใหม่รับงานต่อ\n"
            f"👉 หรือเรียก rider_clear_emergency(rider_id) เพื่อคืนสถานะ Rider เดิม"
        )
        return response
        
        
    except Exception as e:
        return f"Error: เกิดข้อผิดพลาด — {str(e)}"


@mcp.tool()
def rider_clear_emergency(rider_id: str) -> str:
    """
    ══════════════════════════════════════════════════════
    เคลียร์สถานะฉุกเฉินของ Rider (ให้กลับมารับงานได้)
    ══════════════════════════════════════════════════════

    ใช้หลังจาก Rider จัดการเหตุฉุกเฉินเสร็จแล้ว
    เช่น ซ่อมรถเสร็จ, สถานการณ์คลี่คลาย
    """
    rider = shop_bang_korn_67.get_employee(rider_id)
    if not rider or not isinstance(rider, Rider):
        return f"Error: ไม่พบ Rider ID: {rider_id}"

    if not rider.get_emergency_status():
        return f"ℹ️ Rider {rider.get_name()} ไม่มีสถานะฉุกเฉินอยู่"

    old_reason = rider.get_emergency_status()
    rider.clear_emergency()

    return (
        f"✅ เคลียร์สถานะฉุกเฉินสำเร็จ!\n"
        f"   🏍️ Rider: {rider.get_name()} ({rider_id})\n"
        f"   📋 เหตุที่เคยแจ้ง: {old_reason}\n"
        f"   📍 สถานะปัจจุบัน: พร้อมรับงาน ✅"
    )

# ==========================================
# Tool ขั้นที่ 1: WarehouseStock ตรวจชั้นวาง
# ==========================================
@mcp.tool()
def check_shelf_stock() -> str:
    """
    ══════════════════════════════════════════════════════
    ตรวจสอบสต็อกบนชั้นวาง (WarehouseStock ตรวจอัตโนมัติ)
    ══════════════════════════════════════════════════════

    🔒 FLOW RULE:
    ─────────────
    1. tool นี้คือ ขั้นที่ 1 — ระบบตรวจสอบชั้นวาง
    2. ถ้าพบชั้นที่ของน้อยกว่า threshold → ส่ง SystemNotification แจ้ง Staff
    3. Staff เห็นแจ้งเตือนแล้ว → เรียก refill_shelf เป็นขั้นที่ 2

    📝 AFTER THIS TOOL:
    ────────────────────
    - ถ้ามีชั้นที่ต้องเติม → แนะนำให้เรียก refill_shelf
    - ถ้าทุกชั้นปกติ → แจ้งว่าไม่ต้องเติม
    """
    low_stock = shop_bang_korn_67.check_shelf_stock()

    if not low_stock:
        # ตรวจแล้วทุกชั้นปกติ
        all_shelves = shop_bang_korn_67.get_warehouse_stock().get_all_shelf_slots()
        result = "✅ ตรวจสอบแล้ว — ชั้นวางทุกชั้นมีสินค้าเพียงพอ\n\n"
        for slot in all_shelves:
            product = slot.get_product()
            result += (
                f"   📦 {slot.get_slot_id()} | {product.get_name()} "
                f"| {slot.get_current_qty()}/{slot.get_capacity()} "
                f"(threshold: {slot.get_min_threshold()})\n"
            )
        return result

    # มีชั้นที่ต้องเติม
    result = (
        f"⚠️ พบ {len(low_stock)} ชั้นวางที่สินค้าน้อยกว่าเกณฑ์!\n"
        f"═══════════════════════════════════════\n"
        f"📨 ส่ง SystemNotification แจ้ง Staff แล้ว\n\n"
    )

    for i, alert in enumerate(low_stock, 1):
        slot = alert.get_shelf_slot()
        product = slot.get_product()
        result += (
            f"   {i}. 🔴 {slot.get_slot_id()} | {product.get_name()}\n"
            f"      เหลือ: {slot.get_current_qty()}/{slot.get_capacity()} "
            f"(threshold: {slot.get_min_threshold()})\n"
            f"      ต้องเติม: {alert.get_need_refill()} ชิ้น\n"
            f"      Notification: {alert.get_notification_status()}\n\n"
        )

    result += (
        f"═══════════════════════════════════════\n"
        f"👉 Staff เรียก refill_shelf(staff_id, slot_id) เพื่อเติมสินค้า"
    )
    return result


# ==========================================
# Tool ขั้นที่ 2: Staff เติมสินค้า (หลังได้ Notification)
# ==========================================
@mcp.tool()
def refill_shelf(staff_id: str, slot_id: str) -> str:
    """
    ══════════════════════════════════════════════════════
    เติมสินค้าจากคลังไปยังชั้นวาง (Staff เรียกหลังได้ Notification)
    ══════════════════════════════════════════════════════

    🔒 FLOW RULE:
    ─────────────
    1. ต้องเรียก check_shelf_stock ก่อน → ระบบแจ้งว่าชั้นไหนต้องเติม
    2. Staff เห็นแจ้งเตือนแล้ว → เรียก tool นี้เพื่อเติม

    🔧 PARAMETERS:
    ──────────────
    - staff_id:
        • "STF-001" = สมหญิง (Cashier)
        • "STF-002" = สมชาย (Manager)
    - slot_id:
        • "SHELF-001" = Coke      (จุ 20, threshold 5)
        • "SHELF-003" = Beer      (จุ 10, threshold 3)
        • "SHELF-004" = Lay       (จุ 25, threshold 5)
    """
    result = shop_bang_korn_67.refill_shelf_from_warehouse(staff_id, slot_id)

    if result.get_status() == "error":
        return f"Error: {result.get_message()}"

    if result.get_status() == "info":
        return (
            f"ℹ️ {result.get_message()}\n"
            f"   📦 สต็อกบนชั้น: {result.get_extra('current_qty')}/{result.get_extra('capacity')}"
        )

    if result.get_status() == "success":
        return (
            f"✅ เติมสินค้าสำเร็จ!\n"
            f"═══════════════════════════════════════\n"
            f"   🛒 {result.get_message()}\n"
            f"   👨‍💼 เติมโดย: {result.get_extra('staff_name')}\n"
            f"   📦 สต็อกบนชั้น: {result.get_extra('current_qty')}/{result.get_extra('capacity')}\n"
            f"   🏭 เหลือในคลัง: {result.get_extra('warehouse_remaining')} ชิ้น\n"
            f"═══════════════════════════════════════"
        )



# ==========================================
# 5. รันเซิร์ฟเวอร์ MCP
# ==========================================
# ==========================================
# 🧪 ส่วนจำลองรันทดสอบระบบ Barista (Test Script)
# ==========================================
# ==========================================
# 5. รันเซิร์ฟเวอร์ MCP
# ==========================================
if __name__ == "__main__":
    mcp.run()
