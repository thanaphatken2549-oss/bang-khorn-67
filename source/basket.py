from product import Product

class Result:
    """ใช้ส่งผลลัพธ์ระหว่าง method แทน dict"""
    def __init__(self, status: str, message: str = ""):
        self.__status = status
        self.__message = message
        self.__extras = []

    def get_status(self): return self.__status
    def get_message(self): return self.__message

    def set_extra(self, key: str, value):
        for i, (k, v) in enumerate(self.__extras):
            if k == key:
                self.__extras[i] = (key, value)
                return
        self.__extras.append((key, value))

    def get_extra(self, key: str, default=None):
        for k, v in self.__extras:
            if k == key:
                return v
        return default

# --- OrderItem ---
class OrderItem:
    def __init__(self, product: Product, qty):
        if qty <= 0:
            raise ValueError("Quantity must be greater than 0")
        self.__product = product
        self.__qty = qty
        self.__status = "Queued"

    def get_qty(self): return self.__qty
    def get_product_order_item(self) -> Product: return self.__product
    def update_status(self, new_status: str):
        self.__status = new_status
        print(f"   [Barista] แก้ว {self.__product.get_name()} -> {self.__status}")

    def get_status(self) -> str:
        return self.__status

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

    def remove_from_basket(self, product_id: str) -> bool:
        for i, item in enumerate(self.__items):
            if item.get_product_order_item().get_product_id() == product_id:
                self.__items.pop(i)
                return True
        return False

    def clear_basket(self):
        self.__items.clear()
