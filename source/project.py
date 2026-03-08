import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from datetime import datetime, timedelta
from fastmcp import FastMCP

from product import Product, NormalProduct, CafeProduct, AlcoholProduct
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

    def get_member_by_phone(self, phone_number: str):
        return self.get_member(phone_number)

    def create_member(self, phone: str, name: str = "Member Customer",password: str="", age=0, address: str = "", distance_km: float = 0.0):
        self.__member.append(
            Member(phone, name, age=age, address=address,
                    distance_km=distance_km, password=password)
        )

    def add_product(self, product: Product):
        self.__product.append(product)

    def get_product(self):
        return self.__product

    def get_product_by_id(self, product_id: str):
        for product in self.__product:
            if product.get_product_id() == product_id:
                return product
        return None
    
    def get_current_guest(self) -> Customer:
        return self.__current_guest

    def reset_current_guest(self):
        self.__current_guest = Customer()

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
            return {"status": "error", "message": f"ไม่พบ Rider ID: {rider_id}"}

        # ค้นหา Order ที่ Rider กำลังส่ง
        order = self.find_order_by_rider(rider_id)
        if not order:
            return {"status": "error", "message": f"Rider {rider_id} ไม่มี Order ที่กำลังส่งอยู่"}

        # [Seq 2] SC → SC: get_staffid() (self-call หา Staff)
        staff = self.find_available_staff()
        if not staff:
            return {"status": "error", "message": "ไม่พบ Staff ในระบบ"}

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

        # [Seq 8-10] SC → Order: update_status + unassign_rider
        old_rider = order.unassign_rider()
        order.update_status("Waiting for Rider")  # กลับไปรอ Rider คนใหม่

        # [Seq 11] Return success กลับไปให้ Rider
        # [Seq 11] Return
        return {
            "status": "success",
            "order_id": order.get_order_id(),
            "new_order_status": "Waiting for Rider (Re-dispatch)",
            "handled_by": alert_result["handled_by"],
            "rider_released": rider.get_name(),
            "reason": reason,
            # ━━━ 🆕 เพิ่มข้อมูล Notification ━━━
            "system_notification": alert_result["system_notification"],
            "sms_notification": alert_result["sms_notification"],
            "customer_phone": customer_phone
        }
    
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
            return {"status": "error", "message": f"ไม่พบพนักงานรหัส {staff_id}"}
        if not isinstance(staff, Staff):
            return {"status": "error",
                    "message": f"พนักงาน {staff_id} ไม่ใช่ Staff (Barista/Rider เติมไม่ได้)"}

        # 2. ค้นหา ShelfSlot (ผ่าน WarehouseStock)
        shelf_slot = self.__warehouse_stock.find_shelf_slot(slot_id)
        if not shelf_slot:
            return {"status": "error", "message": f"ไม่พบชั้นวาง {slot_id}"}

        # 3. Staff ดำเนินการเติม
        result_status = staff.refill_shelf(shelf_slot, self.__warehouse_stock)

        # 4. แปลผลลัพธ์
        product = shelf_slot.get_product()
        if result_status == "ALREADY_FULL":
            return {
                "status": "info",
                "message": f"ชั้นวาง {slot_id} ({product.get_name()}) เต็มแล้ว",
                "current_qty": shelf_slot.get_current_qty(),
                "capacity": shelf_slot.get_capacity()
            }
        elif result_status == "STATUS_FAILED":
            return {
                "status": "error",
                "message": f"สินค้า {product.get_name()} ในคลังไม่เพียงพอ "
                           f"(เหลือ {product.get_qty()} ชิ้น)",
                "warehouse_remaining": product.get_qty()
            }
        elif result_status == "REFILL_COMPLETED":
            return {
                "status": "success",
                "message": f"เติม {product.get_name()} เข้าชั้นวาง {slot_id} สำเร็จ",
                "current_qty": shelf_slot.get_current_qty(),
                "capacity": shelf_slot.get_capacity(),
                "warehouse_remaining": product.get_qty(),
                "staff_name": staff.get_name()
            }





    
    
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
    """
    ══════════════════════════════════════
    สมัครสมาชิกใหม่
    ══════════════════════════════════════
    สมัครแล้วต้องเรียก login อีกครั้งถึงจะใช้งานได้
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
    """
    ══════════════════════════════════════
    เข้าสู่ระบบ (ต้องเรียกก่อน add_product_to_basket เสมอ)
    ══════════════════════════════════════

    📌 วิธีใช้:
    - login สมาชิก → ใส่ phone + password → สั่งได้ทั้ง ONSITE + ONLINE
    - login Guest  → ไม่ต้องใส่อะไรเลย  → สั่งได้แค่ ONSITE

    🏪 สมาชิกในระบบ:
    - "0915919569" / "vip1234"
    - "0912345678" / "somchai1234"
    - "0898765432" / "somying1234"
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
    """
    ══════════════════════════════════════
    ออกจากระบบ
    ══════════════════════════════════════
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
    """
    ══════════════════════════════════════════════
    ขั้นตอนที่ 1 ของ 3 — เพิ่มสินค้าลงตะกร้า
    ══════════════════════════════════════════════

    🔒 FLOW RULE:
    1. ต้อง login ก่อนเสมอ (ทั้ง Member และ Guest)
    2. ห้ามเรียก process_payment หรือ create_transaction ก่อน tool นี้

    📦 PARAMETERS:
    - product_id: รหัสสินค้า
    - qty: จำนวน
    (ไม่ต้องใส่เบอร์โทร — ระบบรู้จาก session ที่ login ไว้)

    coke = "DR-001"
    coffee = "CF-001"
    beer = "ALC-001"
    lay = "GD-001"
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
    """
    ══════════════════════════════════════════════════════
    ขั้นตอนที่ 2 ของ 3 — สร้าง Order + ชำระเงิน
    ══════════════════════════════════════════════════════

    🔒 FLOW RULE:
    1. ต้อง login + add_product_to_basket ก่อน
    2. Guest สั่งได้แค่ ONSITE
    3. Member สั่งได้ทั้ง ONSITE + ONLINE

    🔧 PARAMETERS:
    - order_type: "onsite" / "online"
    - payment_channel: "cash" / "qr" / "cod"
    - received_amount: จำนวนเงินที่รับ (เฉพาะ cash)
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

        result_msg = f"Success: ออเดอร์สำเร็จ! ยอดรวม {total_price} บาท ({payment_msg})"

        if order_type.upper() == "ONLINE" and isinstance(customer_obj, Member):
            new_order.update_status("Waiting for Rider")
            result_msg += f"\n- ประเภท: ONLINE"
            result_msg += f"\n- ที่อยู่จัดส่ง: {customer_obj.get_address()}"
            result_msg += f"\n- ค่าจัดส่ง: {new_order.get_delivery_fee()} บาท"
            next_step_msg = "\n👉 เรียก rider_accept_order เพื่อให้ Rider มารับงาน"
        else:
            new_order.update_status("Paid")
            result_msg += f"\n- ประเภท: ONSITE"
            next_step_msg = "\n👉 เรียก create_transaction เพื่อออกใบเสร็จ"

        if isinstance(customer_obj, Member):
            earned_points = new_order.calculate_member_point()
            customer_obj.received_point(earned_points)
            customer_obj.clear_basket()
            result_msg += f"\n- สถานะ: สมาชิก ({customer_obj.get_name()})"
            result_msg += f"\n- Tier: {customer_obj.get_tier().get_tier_name()}"
            result_msg += f"\n- ได้ {earned_points} แต้ม (รวม {customer_obj.get_point()} แต้ม)"
        else:
            customer_obj.clear_basket()     
            result_msg += "\n- สถานะ: Guest"

        result_msg += f"\n\n*** ORDER ID: {new_order.get_order_id()} ***"
        result_msg += next_step_msg
        return result_msg
    else:
        return "Error: การชำระเงินล้มเหลว"



@mcp.tool()
def rider_accept_order(rider_id: str) -> str:
    """
    ══════════════════════════════════════════════════════════
    ขั้นตอนพิเศษ — Rider รับงานส่งของ (เฉพาะ Online Order)
    ══════════════════════════════════════════════════════════

    🔒 FLOW RULE (ห้ามฝ่าฝืน):
    ─────────────────────────────
    1. ใช้ tool นี้ได้เฉพาะหลัง create_transaction เสร็จแล้ว
       และ order นั้นเป็นแบบ "online" เท่านั้น
    2. ไม่ต้องระบุ order_id — ระบบค้นหาออเดอร์ที่รอ Rider อัตโนมัติ (FIFO)
    3. ห้ามเรียก tool นี้กับ order แบบ "onsite"

    📝 BEFORE THIS TOOL — AI ต้องทำ:
    ─────────────────────────────────
    - บอกผู้ใช้ว่า "กำลังค้นหาออเดอร์ที่รอ Rider และจับคู่ให้..."
    - อาจเรียก rider_view_pending_orders ก่อนเพื่อดูว่ามีออเดอร์รออยู่ไหม

    📝 AFTER THIS TOOL — สิ่งที่ AI ต้องทำ:
    ─────────────────────────────────────────
    - แสดงผลลัพธ์ทั้งหมด
    - ถ้ามีการเก็บเงิน COD → แจ้งว่า Rider เก็บเงินเรียบร้อย
    - บอกว่า "ต้องการทำรายการอื่นอีกไหม?"

    🔧 PARAMETERS:
    ──────────────
    - rider_id: รหัส Rider
        • "RD-001" = สมศักดิ์ ซิ่งเร็ว (ทะเบียน 1กก-1234)
        • "RD-002" = สมปอง วิ่งไว (ทะเบียน 2ขข-5678)
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
        f"✅ จับคู่สำเร็จ!\n"
        f"   📦 ออเดอร์: {order_id}\n"
        f"   🏍️ Rider: {rider.get_name()} ({rider.get_license_plate()})\n"
        f"   📍 สถานะ: Delivering (กำลังจัดส่ง)"
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🆕 แก้ไข: ไม่เก็บเงิน COD ตรงนี้แล้ว
    #    เก็บเงินตอน rider_confirm_delivery แทน
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    order_payment = order.get_payment()
    if order_payment and order_payment.get_payment_channel().get_channel_type() == "COD":
        result_msg += f"\n   💵 COD: เก็บเงิน {order_payment.get_amount():.2f} บาท เมื่อส่งถึงลูกค้า"

    # แสดงจำนวนออเดอร์ที่ยังรอ Rider อยู่
    remaining = len(pending_orders) - 1
    if remaining > 0:
        result_msg += f"\n\n   ⏳ ยังมีออเดอร์รอ Rider อีก {remaining} รายการ"

    #✅ หลังแก้ — เพิ่มบรรทัดนี้ก่อน return
    result_msg += f"\n\n👉 เมื่อส่งถึงลูกค้าแล้ว → เรียก rider_confirm_delivery"
    return result_msg

@mcp.tool()
def rider_confirm_delivery(rider_id: str) -> str:
    """
    ══════════════════════════════════════════════════════════
    ขั้นตอนพิเศษ — Rider ยืนยันส่งของถึงลูกค้าแล้ว
    ══════════════════════════════════════════════════════════

    🔒 FLOW RULE:
    ─────────────
    1. ใช้ได้หลัง rider_accept_order เท่านั้น (Order status = "Delivering")
    2. ถ้าเป็น COD → ระบบเก็บเงินปลายทาง ณ จุดนี้
    3. หลังยืนยันแล้ว → เรียก create_transaction เพื่อออกใบเสร็จ

    🔧 PARAMETERS:
    ──────────────
    - rider_id: รหัส Rider ที่กำลังส่งของอยู่
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
        f"✅ ยืนยันส่งสำเร็จ!\n"
        f"   📦 Order: {order.get_order_id()}\n"
        f"   🏍️ Rider: {rider.get_name()} ({rider.get_license_plate()})\n"
        f"   📍 สถานะ: Delivered (ส่งถึงลูกค้าแล้ว){cod_msg}\n"
        f"\n👉 เรียก create_transaction เพื่อออกใบเสร็จ"
    )


@mcp.tool()
def create_transaction(staff_id: str, order_id: str) -> str:
    """
    ══════════════════════════════════════════════════════════
    ขั้นตอนที่ 3 — ขั้นตอนสุดท้าย — ออกใบเสร็จ Transaction
    ══════════════════════════════════════════════════════════

    🔒 FLOW RULE (ห้ามฝ่าฝืน):
    ─────────────────────────────
    1. ห้ามเรียก tool นี้ ถ้ายังไม่ผ่านขั้นที่ 1 (add_to_basket) และขั้นที่ 2 (create_order)
    2. order_id ต้องใช้ค่าที่ได้จาก create_order เท่านั้น ห้ามแต่งขึ้นเอง
    3. ข้อความที่ tool นี้ return กลับมา คือ "ใบเสร็จฉบับเต็ม"
       → ห้ามตัดทอน ห้ามดัดแปลง ห้ามสรุปเอง ห้ามย่อ
       → ให้พิมพ์ออกมาแสดงทุกบรรทัดเป๊ะ ๆ

    📝 BEFORE THIS TOOL — AI ต้องทำ:
    ─────────────────────────────────
    - บอกผู้ใช้ว่า "กำลังออกใบเสร็จโดยพนักงาน {staff_id} สำหรับ Order {order_id}..."

    📝 AFTER THIS TOOL — สิ่งที่ AI ต้องทำ:
    ─────────────────────────────────────────
    - แสดงใบเสร็จทั้งหมดที่ return มา (ห้ามสรุป ห้ามย่อ)
    - ถ้า order เป็น "online":
        → บอกว่า "ออเดอร์นี้กำลังรอ Rider มารับงานส่งของครับ"
        → ถ้าผู้ใช้ต้องการให้ Rider รับงาน → ใช้ rider_accept_order
    - ถ้า order เป็น "onsite":
        → บอกว่า "เสร็จสิ้นครับ! ต้องการสั่งรายการอื่นอีกไหม?"
    - Flow จบ — พร้อมเริ่มรอบใหม่ได้

    🔧 PARAMETERS:
    ──────────────
    - staff_id: รหัสพนักงาน Staff (ไม่ใช่ Barista ไม่ใช่ Rider)
        • "STF-001" = สมหญิง รักบริการ (Cashier)
        • "STF-002" = สมชาย ใจเย็น (Manager)
    - order_id: รหัส Order ที่ได้จาก create_order (ห้ามแต่งเอง)
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
        
        result_msg = f"Status: Success\nMessage: Transaction Completed\n\n{receipt}"
        result_msg += f"\n*** TRANSACTION ID: {transaction.get_transaction_id()} ***"
        result_msg += f"\n💡 หากต้องการยกเลิกรายการนี้ภายหลัง ให้เรียกใช้ tool 'void_transaction' พร้อมระบุ transaction_id นี้"

        return result_msg
    except Exception as e:
        return f"Error: {str(e)}"
    
# project.py — เพิ่มต่อจาก @mcp.tool() def create_transaction

@mcp.tool()
def void_transaction(staff_id: str, transaction_id: str, void_reason: str) -> str:
    """
    ══════════════════════════════════════════════════════════════
    Tool พิเศษ — Void (ยกเลิก) Transaction ที่ทำสำเร็จแล้ว
    ══════════════════════════════════════════════════════════════

    🔒 FLOW RULE (ห้ามฝ่าฝืน):
    ─────────────────────────────
    1. tool นี้ ไม่อยู่ใน Flow ปกติ (ขั้น 1-2-3) เป็น tool อิสระแยกต่างหาก
    2. ใช้เฉพาะเมื่อผู้ใช้ "ร้องขอยกเลิก" Transaction ที่ออกใบเสร็จแล้วเท่านั้น
    3. ห้ามใช้แทน create_transaction
    4. ห้ามเรียกเอง ต้องรอผู้ใช้สั่งยกเลิก

    📝 BEFORE THIS TOOL — AI ต้องถามให้ครบ:
    ───────────────────────────────────────────
    - staff_id: ต้องเป็น Staff ที่มี admin_level >= 2
        • STF-001 (admin_level=1) → ❌ ไม่มีสิทธิ์ Void
        • STF-002 (admin_level=2) → ✅ มีสิทธิ์ Void
    - transaction_id: UUID ที่ได้จาก create_transaction
    - void_reason: เหตุผลการยกเลิก (ถามผู้ใช้)

    📝 AFTER THIS TOOL:
    ────────────────────
    - แสดงผลลัพธ์การ Void ทั้งหมด
    - แจ้งว่า stock ถูกคืนแล้ว + เงินถูกคืนแล้ว

    🔧 PARAMETERS:
    ──────────────
    - staff_id: รหัส Staff ที่มีสิทธิ์ Admin (เช่น "STF-002")
    - transaction_id: UUID ของ Transaction ที่ต้องการยกเลิก
    - void_reason: เหตุผล เช่น "ลูกค้าเปลี่ยนใจ"
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

        result_msg = f"Status: Success\nMessage: Transaction Voided Successfully\n\n{void_receipt}"

        # แสดงข้อมูลเพิ่มเติม
        refund_amount = order.get_payment().get_amount()

        result_msg += f"\n📋 สรุปการ Void:"
        result_msg += f"\n- ลูกค้า: {customer.get_name()}"
        result_msg += f"\n- จำนวนเงินที่คืน: {refund_amount:.2f} บาท"
        result_msg += f"\n- สินค้าทั้งหมดถูกคืนกลับ Stock เรียบร้อย"
        result_msg += f"\n- Void โดย: {staff.get_name()} ({staff_id})"
        result_msg += f"\n- เหตุผล: {void_reason}"

        return result_msg

    except Exception as e:
        return f"Error: เกิดข้อผิดพลาดในการ Void — {str(e)}"
    
@mcp.tool()
def get_member_history(phone_number: str) -> str:
    """ดูประวัติ Transaction ของสมาชิก"""
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

# project.py — เพิ่ม MCP Tool (ต่อจาก tool อื่นๆ)

@mcp.tool()
def rider_report_emergency(rider_id: str, reason: str) -> str:
    """
    ══════════════════════════════════════════════════════════════
    Tool พิเศษ — Rider แจ้งเหตุฉุกเฉินระหว่างจัดส่ง
    ══════════════════════════════════════════════════════════════

    🔒 FLOW RULE:
    ─────────────
    1. ใช้ได้เฉพาะเมื่อ Rider กำลังส่ง Order อยู่ (status = "Delivering")
    2. ไม่ต้องระบุ order_id — ระบบค้นหาอัตโนมัติจาก rider_id
    3. หลัง Emergency → Order กลับไปสถานะ "Waiting for Rider"
       → Rider คนใหม่สามารถรับงานต่อผ่าน rider_accept_order ได้

    📝 AFTER THIS TOOL — AI ต้องทำ:
    ─────────────────────────────────
    - แสดงผลลัพธ์ทั้งหมด
    - ถามว่าต้องการให้ Rider คนใหม่รับงานต่อไหม
      → ถ้าใช่ → เรียก rider_accept_order
    - แจ้งว่า Rider เดิมถูกปลดจากงานแล้ว

    🔧 PARAMETERS:
    ──────────────
    - rider_id: รหัส Rider ที่ต้องการแจ้งเหตุ
        • "RD-001" = สมปอง ไวปานกามนิต
        • "RD-002" = สมชาย สายซิ่ง
    - reason: เหตุผล เช่น "รถเสีย", "อุบัติเหตุ", "ฝนตกหนักไปต่อไม่ได้"
    """
    try:
        result = shop_bang_korn_67.report_emergency(rider_id, reason)

        if result["status"] == "error":
            return f"Error: {result['message']}"

        # ━━━ สร้างข้อความผล Notification ━━━
        noti_lines = ""

        # System Notification
        if result["system_notification"] == "success":
            noti_lines += f"   🖥️ แจ้งระบบ (Staff/Admin): ส่งสำเร็จ ✅\n"
        else:
            noti_lines += f"   🖥️ แจ้งระบบ (Staff/Admin): ล้มเหลว ❌\n"

        # SMS Notification
        if result["sms_notification"] == "success":
            noti_lines += f"   📱 SMS ถึงลูกค้า ({result['customer_phone']}): ส่งสำเร็จ ✅\n"
        elif result["sms_notification"] == "no_phone":
            noti_lines += f"   📱 SMS ถึงลูกค้า: ไม่มีเบอร์โทร (Guest) ⚠️\n"
        else:
            noti_lines += f"   📱 SMS ถึงลูกค้า: ล้มเหลว ❌\n"

        response = (
            f"🚨 แจ้งเหตุฉุกเฉินสำเร็จ!\n"
            f"═══════════════════════════════════════\n"
            f"   📦 Order: {result['order_id']}\n"
            f"   🏍️ Rider เดิม: {result['rider_released']}\n"
            f"   📋 เหตุผล: {result['reason']}\n"
            f"   👨‍💼 Staff รับเรื่อง: {result['handled_by']}\n"
            f"   📍 สถานะ Order: {result['new_order_status']}\n"
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

    for i, shelf in enumerate(low_stock, 1):
        result += (
            f"   {i}. 🔴 {shelf['slot_id']} | {shelf['product_name']}\n"
            f"      เหลือ: {shelf['current_qty']}/{shelf['capacity']} "
            f"(threshold: {shelf['threshold']})\n"
            f"      ต้องเติม: {shelf['need_refill']} ชิ้น\n"
            f"      Notification: {shelf['notification_status']}\n\n"
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

    if result["status"] == "error":
        return f"Error: {result['message']}"

    if result["status"] == "info":
        return (
            f"ℹ️ {result['message']}\n"
            f"   📦 สต็อกบนชั้น: {result['current_qty']}/{result['capacity']}"
        )

    if result["status"] == "success":
        return (
            f"✅ เติมสินค้าสำเร็จ!\n"
            f"═══════════════════════════════════════\n"
            f"   🛒 {result['message']}\n"
            f"   👨‍💼 เติมโดย: {result['staff_name']}\n"
            f"   📦 สต็อกบนชั้น: {result['current_qty']}/{result['capacity']}\n"
            f"   🏭 เหลือในคลัง: {result['warehouse_remaining']} ชิ้น\n"
            f"═══════════════════════════════════════"
        )



# ==========================================
# 5. รันเซิร์ฟเวอร์ MCP
# ==========================================
if __name__ == "__main__":
    mcp.run()
