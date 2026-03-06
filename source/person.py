from basket import Basket, OrderItem

# --- Person (Base) ---
class Person:
    def __init__(self, name: str, age: int):
        self.__name = name
        self.__age = age

    def get_name(self) -> str: return self.__name
    def get_age(self) -> int: return self.__age


# --- Customer ---
class Customer(Person):
    def __init__(self, name: str = "Guest", age: int = 0):
        super().__init__(name, age)
        self.__basket = Basket()

    def get_basket(self) -> Basket:
        return self.__basket

    def add_to_basket(self, new_order_item: OrderItem) -> bool:
        self.__basket.add_to_basket(new_order_item)
        return True

    def clear_basket(self):
        self.__basket = Basket()


# --- MemberShipTier Hierarchy ---
# [แก้ไข] เปลี่ยนจาก min_spending → min_points
class MemberShipTier:
    def __init__(self, tier: str, min_points: int, discount_rate: float, free_km: float):
        self.__tier = tier
        self.__min_points_to_upgrade = min_points
        self.__discount_rate = discount_rate
        self.__free_delivery_km = free_km

    def get_tier_name(self): return self.__tier
    def get_min_points(self): return self.__min_points_to_upgrade
    def get_discount_rate(self): return self.__discount_rate
    def get_free_delivery_km(self): return self.__free_delivery_km


class StandardTier(MemberShipTier):
    def __init__(self):
        # Standard: 0% discount, ไม่มี free delivery, สมัครใหม่
        super().__init__("Standard", 0, 0.0, 0.0)


class SilverTier(MemberShipTier):
    def __init__(self):
        # Silver: 3% discount, ไม่มี free delivery, ครบ 250 points
        super().__init__("Silver", 250, 0.03, 0.0)


class GoldTier(MemberShipTier):
    def __init__(self):
        # Gold: 5% discount, ฟรี 3 กม.แรก, ครบ 1000 points
        super().__init__("Gold", 1000, 0.05, 3.0)


# --- Member ---
class Member(Customer):
    def __init__(self, phone: str, name: str = "Member Customer", age: int = 0, address: str = "", distance_km: float = 0.0):
        super().__init__(name, age)
        self.__phone = phone
        self.__point = 0
        self.__address = address
        self.__distance_km = distance_km
        self.__current_tier = StandardTier()
        self.__transaction_history = []

    def get_my_phone(self): return self.__phone
    def get_tier(self) -> MemberShipTier: return self.__current_tier
    def get_address(self) -> str: return self.__address
    def get_distance_km(self) -> float: return self.__distance_km

    def received_point(self, point: int) -> bool:
        self.__point += point
        self._check_tier_upgrade()
        return True

    def get_point(self) -> int: return self.__point

    def _check_tier_upgrade(self):
        if self.__point >= 1000:
            if not isinstance(self.__current_tier, GoldTier):
                self.__current_tier = GoldTier()
        elif self.__point >= 250:
            if not isinstance(self.__current_tier, SilverTier):
                self.__current_tier = SilverTier()

# --- Employee ---
class Employee(Person):
    def __init__(self, employee_id: str, name: str, age: int):
        super().__init__(name, age)
        self.__employee_id = employee_id

    def get_employee_id(self): return self.__employee_id

# --- ให้วางต่อจากคลาส Employee (ประมาณบรรทัด 137) ---
class Rider(Employee):
    def __init__(self, employee_id: str, name: str, age: int, license_plate: str, rate_per_km: float = 10.0):
        super().__init__(employee_id, name, age)
        self.__license_plate = license_plate
        self.__rate_per_km = rate_per_km
        self.__is_available = True

    def get_license_plate(self): return self.__license_plate
    def is_available(self): return self.__is_available
    def set_available(self, status: bool): self.__is_available = status

    def calculate_delivery_fee(self, distance_km: float) -> float:
        # คิดค่าส่งเริ่มต้น 20 บาท + (กิโลเมตรละ * เรท)
        return 20.0 + (distance_km * self.__rate_per_km)

# --- BaristaSlot ---
class BaristaSlot:
    def __init__(self):
        self.__status = "available"
        self.__order_drinks = []
        self.__max_drink_slot = 10

    def get_current_load(self) -> int:
        return sum(item.get_qty() for item in self.__order_drinks)

    def can_accept(self, new_drinks_qty: int) -> bool:
        return (self.get_current_load() + new_drinks_qty) <= self.__max_drink_slot

    def add_order(self, order_items: list):
        for item in order_items:
            if item.get_product_order_item().validate_cafe_drink():
                self.__order_drinks.append(item)
        if self.get_current_load() >= self.__max_drink_slot:
            self.__status = "busy"


# --- Barista ---
class Barista(Employee):
    def __init__(self, employee_id: str, name: str, age: int = 0):
        super().__init__(employee_id, name, age)
        self.__barista_slot = BaristaSlot()

    def check_queue_barista(self) -> int:
        return self.__barista_slot.get_current_load()

    def can_accept_order(self, drinks_qty: int) -> bool:
        return self.__barista_slot.can_accept(drinks_qty)

    def assign_drinks(self, order_items: list):
        self.__barista_slot.add_order(order_items)
