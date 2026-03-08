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

    
    def is_available(self, qty: int) -> bool:
        if qty > self.__stock_qty:
            return False
        return True
    
    def deduct_stock(self, amount: int):
        self.__stock_qty -= amount
    
    # product.py — เพิ่มใน class Product ต่อจาก deduct_stock

    def restock_product(self, qty: int):
        """เมธอดหลักที่ถูกเรียกจาก Transaction.restock_related_order()"""
        self.__stock_qty += qty
        return True




class NormalProduct(Product):
    """สินค้าทั่วไป เช่น ขนม น้ำดื่ม ของใช้ ไม่มีข้อจำกัดการซื้อ"""
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
    
    def validate_sale_time(self, current_time: datetime) -> bool:
        t = current_time.time()
        if (time(11, 0) <= t <= time(14, 0)) or (time(17, 0) <= t <= time(23, 59, 59, 999999)):
            return True
        return False



class IngredientProduct(Product):
    def __init__(self, product_id, name, price, stock_qty):
        super().__init__(product_id, name, price, stock_qty)


class RecipeIngredient:
    """เก็บความสัมพันธ์ระหว่าง IngredientProduct กับปริมาณที่ใช้ต่อแก้ว"""
    def __init__(self, ingredient, qty_per_cup: int):
        self.__ingredient = ingredient
        self.__qty_per_cup = qty_per_cup

    def get_ingredient(self):
        return self.__ingredient

    def get_qty_per_cup(self) -> int:
        return self.__qty_per_cup

    def set_qty_per_cup(self, qty: int):
        self.__qty_per_cup = qty


class Recipe:
    def __init__(self):
        self.__ingredients = []  # [RecipeIngredient, ...]

    def add_ingredient(self, ing, qty: int):
        for recipe_ing in self.__ingredients:
            if recipe_ing.get_ingredient() == ing:
                recipe_ing.set_qty_per_cup(qty)
                return
        self.__ingredients.append(RecipeIngredient(ing, qty))

    def get_ingredients(self):
        return [ri.get_ingredient() for ri in self.__ingredients]

    def get_quantity_of_ingredient(self, ing) -> int:
        for ri in self.__ingredients:
            if ri.get_ingredient() == ing:
                return ri.get_qty_per_cup()
        return 0

class CafeProduct(Product):
    def __init__(self, product_id, name, price, stock_qty):
        super().__init__(product_id, name, price, stock_qty)
        self.__recipe = Recipe()
    def add_ingredient(self, ing, qty: int):
        self.__recipe.add_ingredient(ing, qty)

    def get_recipe(self) -> Recipe:
        return self.__recipe
    def validate_cafe_drink(self) -> bool:
        return True