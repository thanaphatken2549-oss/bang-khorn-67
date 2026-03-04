from fastmcp import FastMCP
from datetime import datetime, time

# สร้างเซิร์ฟเวอร์ MCP แทน FastAPI
mcp = FastMCP("Shop_Bang_Korn_67_System")

# ==========================================
# 1. Models & Participants (Classes) - เหมือนเดิม 100%
# ==========================================
class Member:
    def __init__(self, phone: str):
        self.__phone = phone
        self.__basket = Basket()
    def get_basket(self): return self.__basket
    def get_my_phone(self): return self.__phone

class Product:
    def __init__(self, product_id, name, price, stock_qty):
        self.__product_id = product_id
        self.__name = name
        self.__price = price
        self.__stock_qty = stock_qty
    def get_price(self): return self.__price
    def get_product_id(self): return self.__product_id
    def validate_alcohol(self) -> bool:
        return self.__product_id.startswith("ALC")
    def validate_sale_time(self, current_time: datetime) -> bool:
        t = current_time.time()
        if (time(11, 0) <= t <= time(14, 0)) or (time(17, 0) <= t <= time(23, 59, 59)):
            return True
        return False 
    def is_available(self, qty: int) -> bool:
        if self.__product_id == "OUT" or qty > self.__stock_qty: return False
        return True
    def get_qty(self): return self.__stock_qty
    def get_name(self): return self.__name

class Basket:
    def __init__(self): self.__items = []
    def get_basket_items(self): return self.__items
    def create_order_item(self, product, qty): return OrderItem(product, qty)
    def add_to_basket(self, new_order_item) -> bool:
        self.__items.append(new_order_item)
        return True

class OrderItem:
    def __init__(self, product: Product, qty):
        self.__product = product
        self.__qty = qty
        self.__unit_price = product.get_price()
    def get_qty(self): return self.__qty
    def get_product_order_item(self): return self.__product

class ShopController:
    def __init__(self):
        self.__member = []
        self.__product = []
    def get_member_by_phone(self, phone_member: str):
        for each_member in self.__member:
            if each_member.get_my_phone() == phone_member: return each_member
        return False
    def create_member(self, phone: str): self.__member.append(Member(phone))
    def get_product(self): return self.__product
    def add_product(self, product: Product): self.__product.append(product)

# ==========================================
# 2. Setup Mock Data
# ==========================================
shop_bang_korn_67 = ShopController()
shop_bang_korn_67.create_member("0915919569")
coke = Product("DR-001", "Coke", 20, 100)
beer = Product("ALC-001", "Beer", 60, 100)
lay = Product("GD-001", "Lay", 45, 100)
shop_bang_korn_67.add_product(coke)
shop_bang_korn_67.add_product(beer)
shop_bang_korn_67.add_product(lay)

# ==========================================
# 3. Tool สำหรับ Claude (แปลงมาจาก FastAPI Route)
# ==========================================
# ใช้ @mcp.tool() และแตก parameter ออกมาให้ AI ส่งง่ายๆ
@mcp.tool()
def add_product_to_basket(product_id: str, qty: int, phone_member: str) -> str:
    """
    ฟังก์ชันสำหรับให้ลูกค้าหยิบสินค้าใส่ตะกร้า 
    ต้องส่ง รหัสสินค้า (product_id), จำนวน (qty), และเบอร์โทรสมาชิก (phone_member)
    """
    member_obj = shop_bang_korn_67.get_member_by_phone(phone_member)
    if not member_obj:
        return "Error: ไม่พบเบอร์โทรสมาชิกนี้ในระบบ"

    basket = member_obj.get_basket()
    
    selected_product = None
    for each_product in shop_bang_korn_67.get_product():
        if each_product.get_product_id() == product_id:
           selected_product = each_product
           
    if not selected_product:
        return f"Error: ไม่พบสินค้าหมายเลข {product_id} ในร้าน"
        
    is_alcohol = selected_product.validate_alcohol()
    if is_alcohol:                                                      
        current_time = datetime.now()                                                                                
        is_valid_time = selected_product.validate_sale_time(current_time)                           
        if not is_valid_time:
            # แทนที่จะ raise HTTPException ก็ให้ return เป็นข้อความอธิบายให้ AI รู้
            return "Error: ไม่สามารถเพิ่มลงตะกร้าได้ เนื่องจากกฎหมายกำหนดให้ขายแอลกอฮอล์ได้เฉพาะ 11:00-14:00 และ 17:00-24:00 น. เท่านั้น"

    is_avail = selected_product.is_available(qty)
    if not is_avail:
        return "Error: สินค้ามีไม่เพียงพอ หรือหมดสต็อก"
        
    new_order_item = basket.create_order_item(selected_product, qty)
    success = basket.add_to_basket(new_order_item)
    
    if success:
        count = sum(item.get_qty() for item in basket.get_basket_items())
        return f"Success: เพิ่ม {selected_product.get_name()} จำนวน {qty} ชิ้น ลงตะกร้าของเบอร์ {phone_member} เรียบร้อยแล้ว (ปัจจุบันในตะกร้ามีสินค้าทั้งหมด {count} ชิ้น)"

if __name__ == "__main__":
    # รันเซิร์ฟเวอร์แบบ stdio เพื่อให้ Claude เข้ามาเชื่อมต่อ
    mcp.run()