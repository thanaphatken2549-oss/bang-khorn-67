from datetime import datetime, timedelta
from fastmcp import FastMCP

from product import Product, NormalProduct, CafeProduct, AlcoholProduct
from person import Customer, Member, Barista, Rider
from transaction import Order, OnsiteOrder, OnlineOrder, PaymentChannel, QRPayment, CashPayment, Payment


# ==========================================
# 1. Classes & Participants (OOP Models)
# ==========================================

# --- ShopController ---
class ShopController:
    def __init__(self):
        self.__member = []
        self.__product = []
        self.__barista = []
        self.__current_guest = Customer()
        self.__riders = [] # เพิ่ม List สำหรับเก็บ Rider

    def get_member(self, phone_number: str):
        for member in self.__member:
            if member.get_my_phone() == phone_number:
                return member
        return None

    def get_member_by_phone(self, phone_number: str):
        return self.get_member(phone_number)

    def create_member(self, phone: str, name: str = "Member Customer", address: str = "", distance_km: float = 0.0):
        self.__member.append(Member(phone, name, address=address, distance_km=distance_km))

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
    
    def add_rider(self, rider: Rider):
        self.__riders.append(rider)

    def get_available_rider(self):
        for rider in self.__riders:
            if rider.is_available():
                return rider
        return None

# ==========================================
# 2. Init MCP Server
# ==========================================
mcp = FastMCP("Shop_Bang_Korn_67_System")

# ==========================================
# 3. Database Mock
# ==========================================
shop_bang_korn_67 = ShopController()
shop_bang_korn_67.add_barista(Barista("EMP-001", "John (Barista 1)"))
# --- โค้ดที่เพิ่มใหม่ ---
rider1 = Rider("RD-001", "สมปอง ไวปานกามนิต", 30, "1กข 1234 กทม")
rider2 = Rider("RD-002", "สมชาย สายซิ่ง", 25, "9ฮฮ 9999 กทม")
shop_bang_korn_67.add_rider(rider1)
shop_bang_korn_67.add_rider(rider2)
# ---------------------

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
    address="99/9 KMITL ถ.ฉลองกรุง ลาดกระบัง กรุงเทพฯ 10520",
    distance_km=1.0
)
shop_bang_korn_67.create_member(
    "0912345678", "คุณสมชาย ใจดี",
    address="123/45 ซ.ลาดกระบัง 1 แขวงลาดกระบัง เขตลาดกระบัง กรุงเทพฯ 10520",
    distance_km=2.5
)

shop_bang_korn_67.create_member(
    "0898765432", "คุณสมหญิง รักดื่ม",
    address="789 หมู่บ้านพฤกษา ถ.ฉลองกรุง ลาดกระบัง กรุงเทพฯ 10520",
    distance_km=5.0
)


# ==========================================
# 4. MCP Tools
# ==========================================

# [แก้ไข] ปรับ description ให้ AI รู้ว่าต้องเรียก tool นี้ก่อน process_payment เสมอ
@mcp.tool()
def add_product_to_basket(product_id: str, qty: int, phone_member: str = "") -> str:
    """
    [ขั้นตอนที่ 1 - ต้องเรียกก่อน process_payment เสมอ]
    ฟังก์ชันสำหรับให้ลูกค้าหยิบสินค้าใส่ตะกร้า
    ต้องส่ง:
    - product_id: รหัสสินค้า (เช่น "DR-001", "CF-001", "ALC-001", "GD-001")
    - qty: จำนวน
    - phone_member: เบอร์โทรสมาชิก (ถ้าเป็น Guest ให้ใส่ "" หรือไม่ต้องระบุ)

    สินค้าที่มีในร้าน:
    - DR-001: Coke (20 บาท)
    - CF-001: Iced Latte (65 บาท)
    - ALC-001: Beer (60 บาท) - ขายได้เฉพาะ 11:00-14:00 และ 17:00-24:00
    - GD-001: Lay (45 บาท)

    หมายเหตุ: ต้องเรียก tool นี้อย่างน้อย 1 ครั้ง ก่อนเรียก process_payment และ ต้องถามหา phone_member ก่อนดำเนินการใส่สินค้าลงตระกร้าทุกครั้ง ถ้าไม่มี phone_member ให้เป็น Guest ให้ใส่ "" หรือไม่ต้องระบุที่ phone_member
    """
    if phone_member and phone_member.strip() != "":
        customer_obj = shop_bang_korn_67.get_member_by_phone(phone_member)
        if not customer_obj:
            return f"Error: ไม่พบเบอร์โทรสมาชิก {phone_member} ในระบบ"
    else:
        customer_obj = shop_bang_korn_67.get_current_guest()

    basket = customer_obj.get_basket()

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
        customer_label = f"เบอร์ {phone_member}" if phone_member.strip() else "ลูกค้าทั่วไป (Guest)"
        return f"Success: เพิ่ม {selected_product.get_name()} จำนวน {qty} ชิ้น ลงตะกร้าของ{customer_label} เรียบร้อยแล้ว (ปัจจุบันในตะกร้ามีสินค้าทั้งหมด {count} ชิ้น) — พร้อมชำระเงินได้โดยเรียก process_payment"


# [แก้ไข] ปรับ description ให้ AI รู้ว่าต้องเรียก add_product_to_basket ก่อน
@mcp.tool()
def process_payment(payment_channel: str, received_amount: float = 0.0, phone_number: str = "", order_type: str = "ONSITE") -> str:
    """
    [ขั้นตอนที่ 2 - ต้องเรียก add_product_to_basket ก่อนเสมอ]
    ฟังก์ชันสำหรับชำระเงิน (Checkout)

    ข้อกำหนดสำคัญ: ห้ามเรียก tool นี้โดยตรง ต้องเรียก add_product_to_basket ก่อนอย่างน้อย 1 ครั้ง

    ต้องระบุ:
    - payment_channel: "QR" (สแกนจ่าย) หรือ "CASH" (เงินสด)
    - received_amount: จำนวนเงินที่รับมา (กรณีจ่ายเงินสด ถ้าจ่าย QR ปล่อยเป็น 0)
    - phone_number: เบอร์โทรศัพท์สมาชิก (ถ้าเป็นลูกค้าทั่วไป ให้ใส่ "")
    - order_type: "ONSITE" (ซื้อที่ร้าน) หรือ "ONLINE" (สั่งออนไลน์ — ต้องเป็น Member เท่านั้น)
    """
    if phone_number and phone_number.strip() != "":
        customer_obj = shop_bang_korn_67.get_member(phone_number)
        if not customer_obj:
            return f"Error: ไม่พบเบอร์โทรสมาชิก {phone_number} ในระบบ"
    else:
        customer_obj = shop_bang_korn_67.get_current_guest()

    # ===== เพิ่ม: ตรวจสอบสิทธิ์สั่ง ONLINE =====
    if order_type.upper() == "ONLINE":
        if not isinstance(customer_obj, Member):
            return "Error: การสั่งแบบ ONLINE สงวนสิทธิ์เฉพาะสมาชิก (Member) เท่านั้น กรุณาสมัครสมาชิกก่อน"
        if not customer_obj.get_address():
            return "Error: สมาชิกยังไม่ได้ตั้งค่าที่อยู่จัดส่ง ไม่สามารถสั่งแบบ ONLINE ได้"
    # =============================================

    basket = customer_obj.get_basket()
    items = basket.get_basket_items()

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

    # ===== แก้ไข: ส่ง order_type ให้ create_order ตัดสินใจสร้าง Onsite/Online =====
    new_order = shop_bang_korn_67.create_order(customer_obj, order_type.upper())
    assigned_rider = None
    if order_type.upper() == "ONLINE":
        assigned_rider = shop_bang_korn_67.get_available_rider()
        if not assigned_rider:
            return "Error: ขณะนี้ไม่มีพนักงานจัดส่งว่างให้บริการ กรุณาทำรายการใหม่ภายหลัง"
        
        # ส่ง Rider เข้าไปเพื่อคำนวณค่าส่ง และ Assign งานให้รถคันนั้น
        total_price = new_order.calculate_total(vehicle=assigned_rider)
        new_order.assign_rider(assigned_rider)
        assigned_rider.set_available(False) # ล็อกรถคันนี้ว่าไม่ว่างแล้ว
    else:
        total_price = new_order.calculate_total()
    # ==============================================================================

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

    if new_order.check_payment_status():
        if assigned_barista:
            assigned_barista.assign_drinks(items)

        for item in items:
            product = item.get_product_order_item()
            product.deduct_stock(item.get_qty())

        result_msg = f"Success: ชำระเงินสำเร็จ! ยอดรวม {total_price} บาท ({payment_msg})"

        # ===== เพิ่ม: แสดงข้อมูลจัดส่งถ้าเป็น ONLINE =====
        if order_type.upper() == "ONLINE" and isinstance(customer_obj, Member):
            result_msg += f"\n- ประเภท: สั่งออนไลน์ (ONLINE)"
            result_msg += f"\n- ที่อยู่จัดส่ง: {customer_obj.get_address()}"
            result_msg += f"\n- ระยะทาง: {customer_obj.get_distance_km()} กม."
            result_msg += f"\n- 🛵 พนักงานจัดส่ง: {assigned_rider.get_name()}"
            result_msg += f"\n- 🏍️ ทะเบียนรถ: {assigned_rider.get_license_plate()}"
            result_msg += f"\n- 💸 ค่าจัดส่งที่รวมในยอด: {new_order.get_delivery_fee()} บาท"
        else:
            result_msg += f"\n- ประเภท: ซื้อที่ร้าน (ONSITE)"
        # ==================================================

        if isinstance(customer_obj, Member):
            earned_points = new_order.calculate_member_point()
            customer_obj.received_point(earned_points)
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
