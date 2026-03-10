from mcp.server.fastmcp import FastMCP

# สร้าง Server Object ของ FastMCP (อ้างอิงจาก Slide 18)
mcp = FastMCP("BaristaSystem")

# ==========================================
# 1. Models & Participants (Classes)
# ==========================================

class IngredientProduct:
    def __init__(self, ing_id: str, name: str):
        self.__ing_id = ing_id
        self.__name = name

    def get_name(self):
        return self.__name
    
    def get_ing_id(self):
        return self.__ing_id

# --- เพิ่ม Class Recipe ตาม Sequence Diagram ใหม่ ---
class Recipe:
    def __init__(self):
        self.__ingredients = {}  # {IngredientProduct: qty}

    def add_ingredient(self, ing: IngredientProduct, qty: int):
        self.__ingredients[ing] = qty

    def get_ingredients(self):
        """ เทียบเท่าการ loop ขอ get_ingredient() """
        return list(self.__ingredients.keys())

    def get_quantity_of_ingredient(self, ing: IngredientProduct):
        """ คืนค่าปริมาณที่ต้องใช้ของวัตถุดิบนั้นๆ """
        return self.__ingredients.get(ing, 0)

class DrinkProduct:
    def __init__(self, prod_id: str, name: str):
        self.__prod_id = prod_id
        self.__name = name
        self.__recipe = Recipe()  # เปลี่ยนมาเก็บเป็น Object ของ Recipe

    def add_ingredient(self, ing: IngredientProduct, qty: int):
        self.__recipe.add_ingredient(ing, qty)

    def get_name(self):
        return self.__name

    def get_recipe(self):
        return self.__recipe

class DrinkOrderItem:
    def __init__(self, order_id: str, product_name: str):
        self.__order_id = order_id
        self.__product_name = product_name
        self.__status = "Queued"

    def get_name(self):
        return self.__product_name

    def update_status(self, new_status: str):
        self.__status = new_status
        print(f"   [Order {self.__order_id}] Status -> {self.__status}")

class WarehouseStock:
    def __init__(self):
        self.__stock = {}  # {IngredientProduct: qty}

    def add_stock(self, ing: IngredientProduct, qty: int):
        self.__stock[ing] = self.__stock.get(ing, 0) + qty

    def check_ingredient(self, recipe: Recipe) -> bool:
        """ 4. เช็ควัตถุดิบโดยดึงข้อมูลจาก Recipe Object """
        for ing in recipe.get_ingredients():
            required_qty = recipe.get_quantity_of_ingredient(ing)
            if self.__stock.get(ing, 0) < required_qty:
                return False
        return True

    def deduct(self, ing: IngredientProduct, qty: int):
        if self.__stock.get(ing, 0) >= qty:
            self.__stock[ing] -= qty
            print(f"   🏭 [Warehouse] Deducted {ing.get_name()}: {qty} (Left: {self.__stock[ing]})")
            return True
        return False

class BaristaSlot:
    def __init__(self):
        self.__orders = []

    def add_order(self, order: DrinkOrderItem):
        self.__orders.append(order)

    def get_first_order(self):
        return self.__orders[0] if self.__orders else None

    def remove_first_order(self):
        if self.__orders:
            removed = self.__orders.pop(0)
            print(f"   🗑️ [Slot] Removed Order from Queue")

class Barista:
    def __init__(self, barista_id: str, name: str):
        self.__barista_id = barista_id
        self.__name = name
        self.__slot = BaristaSlot()

    def get_barista_id(self):
        return self.__barista_id

    def get_name(self):
        return self.__name

    def get_slot(self):
        return self.__slot

    def barista_make(self, recipe: Recipe, warehouse: WarehouseStock, order_item: DrinkOrderItem):
        """ รับผิดชอบขั้นตอนที่ 5 - 7 ตาม Sequence Diagram """
        # 5. สั่งตัดสต็อก (ลูปตัดทีละวัตถุดิบ)
        for ing in recipe.get_ingredients():
            qty = recipe.get_quantity_of_ingredient(ing)
            warehouse.deduct(ing, qty)
            
        # 6. สั่ง Machine เปลี่ยนสถานะ
        order_item.update_status("Preparing")
        order_item.update_status("Ready")
        
        # 7. เคลียร์คิว
        self.__slot.remove_first_order()


class ShopController:
    def __init__(self):
        self.__baristas = []
        self.__products = []
        self.__warehouse = WarehouseStock()

    def add_barista(self, barista: Barista):
        self.__baristas.append(barista)

    def add_product(self, product: DrinkProduct):
        self.__products.append(product)

    def get_warehouse(self):
        return self.__warehouse

    def get_barista(self, barista_id: str):
        for b in self.__baristas:
            if b.get_barista_id() == barista_id:
                return b
        return None

    def find_product(self, name: str):
        for p in self.__products:
            if p.get_name() == name:
                return p
        return None

    def start_job(self, barista_id: str):
        """ 1. Actor สั่งเริ่มงาน """
        # 2. ค้นหา Barista Object
        barista = self.get_barista(barista_id)
        if not barista:
            return "Barista Not Found"

        # 3. Barista ดึงใบออเดอร์
        order_item = barista.get_slot().get_first_order()
        if not order_item:
            return "No orders in queue"

        # 4. ขอสูตรและตรวจสอบ
        product = self.find_product(order_item.get_name())
        if not product:
            return "Product Not Found"
        
        recipe = product.get_recipe()

        # ตรวจสอบว่าวัตถุดิบพอหรือไม่
        is_enough = self.__warehouse.check_ingredient(recipe)

        if not is_enough:
            return "Show 'not enough ing'"
        else:
            # alt enough
            # ส่งหน้าที่ให้ Barista ทำงาน (ตัดสต็อก, ปรับ status, ลบคิว)
            barista.barista_make(recipe, self.__warehouse, order_item)

            return f"Show 'Ready' - {order_item.get_name()} served by {barista.get_name()}"


# ==========================================
# 2. Setup Initial Data
# ==========================================
shop = ShopController()

# วัตถุดิบ
coffee_bean = IngredientProduct("ING-01", "Coffee Bean")
milk = IngredientProduct("ING-02", "Milk")

# สูตรเครื่องดื่ม
latte = DrinkProduct("DR-01", "Latte")
latte.add_ingredient(coffee_bean, 2)
latte.add_ingredient(milk, 5)
shop.add_product(latte)

# สต็อก
shop.get_warehouse().add_stock(coffee_bean, 100)
shop.get_warehouse().add_stock(milk, 100)

# พนักงานและออเดอร์
john = Barista("EMP-01", "John Wick")
shop.add_barista(john)

order1 = DrinkOrderItem("ORD-999", "Latte")
john.get_slot().add_order(order1)


# ==========================================
# 3. FastMCP Tools & Resources
# ==========================================

@mcp.tool()
def start_job(barista_id: str) -> str:
    """
    ฟังก์ชันสำหรับสั่งให้ Barista ดึงออเดอร์คิวแรกมาทำ (Actor สั่งเริ่มงาน)
    """
    return shop.start_job(barista_id)

@mcp.resource("config://shop/warehouse")
def get_warehouse_stock() -> str:
    """
    ฟังก์ชันแบบ Resource สำหรับให้ AI เช็คจำนวนวัตถุดิบปัจจุบันทั้งหมดในโกดัง
    """
    stock_info = []
    # ดึงข้อมูลจาก stock dictionary
    for ing, qty in shop.get_warehouse()._WarehouseStock__stock.items():
        stock_info.append(f"{ing.get_name()}: {qty}")
    return "\n".join(stock_info) if stock_info else "Warehouse is empty."


if __name__ == "__main__":
    # สั่งรัน MCP Server
    mcp.run()
