from datetime import datetime, time

# --- Product Hierarchy ---
class Product:
    def __init__(self, product_id, name, price, stock_qty):
        self.__product_id = product_id
        self.__name = name
        self.__price = price
        self.__stock_qty = stock_qty

    def get_price(self): return self.__price
    def get_product_id(self): return self.__product_id
    def get_name(self): return self.__name
    def get_qty(self): return self.__stock_qty

    def validate_alcohol(self) -> bool:
        return False

    def validate_cafe_drink(self) -> bool:
        return False

    def validate_sale_time(self, current_time: datetime) -> bool:
        t = current_time.time()
        if (time(11, 0) <= t <= time(14, 0)) or (time(17, 0) <= t <= time(23, 59, 59)):
            return True
        return False

    def is_available(self, qty: int) -> bool:
        if self.__product_id == "OUT" or qty > self.__stock_qty:
            return False
        return True
    
    def deduct_stock(self, amount: int):
        self.__stock_qty -= amount


class NormalProduct(Product):
    pass


class AlcoholProduct(Product):
    def __init__(self, product_id, name, price, stock_qty, alcohol_percentage: str = "5%"):
        super().__init__(product_id, name, price, stock_qty)
        self.__alcohol_percentage = alcohol_percentage
        self.__restricted_age = 20

    def get_restricted_age(self) -> int:
        return self.__restricted_age

    def validate_alcohol(self) -> bool:
        return True


class IngredientProduct(Product):
    def __init__(self, product_id, name, price, stock_qty):
        super().__init__(product_id, name, price, stock_qty)


class CafeProduct(Product):
    def __init__(self, product_id, name, price, stock_qty):
        super().__init__(product_id, name, price, stock_qty)
        self.__size = ["S", "M", "L"]

    def validate_cafe_drink(self) -> bool:
        return True

