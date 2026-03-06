from product import Product

# --- OrderItem ---
class OrderItem:
    def __init__(self, product: Product, qty):
        self.__product = product
        self.__qty = qty
        self.__unit_price = product.get_price()

    def get_qty(self): return self.__qty
    def get_product_order_item(self) -> Product: return self.__product


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
