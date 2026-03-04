from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time
import uvicorn

app = FastAPI()

# ==========================================
# 1. Models สำหรับ Request
# ==========================================
class CheckoutRequest(BaseModel):
    phone_number: Optional[str] = None
    payment_channel: str
    received_amount: float = 0.0

# ==========================================
# 2. Classes & Participants
# ==========================================
class Product:
    def __init__(self, product_id, name, price, stock_qty):
        self.__product_id = product_id
        self.__name = name
        self.__price = price
        self.__stock_qty = stock_qty

    def get_price(self): return self.__price
    def get_product_id(self): return self.__product_id
    def get_name(self): return self.__name
    
    def create_order_item(self, qty):
        return OrderItem(self, qty)
    
    def validate_alcohol(self) -> bool:
        return self.__product_id.startswith("ALC")

    def validate_cafe_drink(self) -> bool:
        return self.__product_id.startswith("CF")

    def validate_sale_time(self, current_time: datetime) -> bool:
        t = current_time.time()
        if (time(11, 0) <= t <= time(14, 0)) or (time(17, 0) <= t <= time(23, 59, 59)):
            return True
        return False 

    def is_available(self, qty: int) -> bool:
        if self.__product_id == "OUT" or qty > self.__stock_qty:
            return False
        return True

class OrderItem:
    def __init__(self, product: Product, qty):
        self.__product = product
        self.__qty = qty
        self.__unit_price = product.get_price()
    
    def get_qty(self): return self.__qty
    def get_product_order_item(self) -> Product: return self.__product

class Basket:
    def __init__(self):
        self.__items = []

    def get_basket_items(self): return self.__items
    
    def set_item(self, order_item: OrderItem):
        self.__items.append(order_item)

    def count_drink_items(self) -> int:
        count = 0
        for item in self.__items:
            product = item.get_product_order_item()
            if product.validate_cafe_drink():
                count += item.get_qty()
        return count

class Customer:
    def __init__(self):
        self.__basket = Basket()

    def get_basket(self) -> Basket:
        return self.__basket

    def add_to_basket(self, new_order_item: OrderItem) -> bool:
        self.__basket.set_item(new_order_item)
        return True
        
    def clear_basket(self):
        self.__basket = Basket()

class Member(Customer):
    def __init__(self, phone: str):
        super().__init__()
        self.__phone = phone
        self.__point = 0 

    def get_my_phone(self): return self.__phone

    def received_point(self, point: int) -> bool:
        self.__point += point
        return True

    def get_point(self) -> int: return self.__point

class Employee:
    def __init__(self, employee_id):
        self.__employee_id = employee_id

class BaristaSlot:
    def __init__(self):
        self.__status = "available"
        self.__order_drinks = []
        self.__max_drink_slot = 10
        
    def get_current_load(self) -> int:
        total_drinks = sum(item.get_qty() for item in self.__order_drinks)
        return total_drinks
        
    def can_accept(self, new_drinks_qty: int) -> bool:
        return (self.get_current_load() + new_drinks_qty) <= self.__max_drink_slot

    def add_order(self, order_items: list):
        for item in order_items:
            if item.get_product_order_item().validate_cafe_drink():
                self.__order_drinks.append(item)
        
        if self.get_current_load() >= self.__max_drink_slot:
            self.__status = "busy"

class Barista(Employee):
    def __init__(self, employee_id: str, name: str):
        super().__init__(employee_id)
        self.__name = name
        self.__barista_slot = BaristaSlot() 

    def check_queue_barista(self) -> int:
        return self.__barista_slot.get_current_load()
        
    def can_accept_order(self, drinks_qty: int) -> bool:
        return self.__barista_slot.can_accept(drinks_qty)
        
    def assign_drinks(self, order_items: list):
        self.__barista_slot.add_order(order_items)


class OnsiteOrder:
    def __init__(self, customer: Customer, order_type: str):
        self.__customer = customer 
        self.__basket = customer.get_basket() 
        self.__order_type = order_type
        self.__total_price = 0.0
        self.__is_paid = False

    def get_customer(self) -> Customer:
        return self.__customer

    def calculate_total(self) -> float:
        total = 0
        for item in self.__basket.get_basket_items():
            total += (item.get_product_order_item().get_price() * item.get_qty())
        self.__total_price = total
        return total

    def set_paid_status(self, status: bool):
        self.__is_paid = status

    def check_payment_status(self) -> bool:
        return self.__is_paid

    def calculate_member_point(self) -> int:
        return int(self.__total_price // 10)


# --- [แก้ไข] ระบบ Payment ตามหลัก Inheritance & Composition ---

# 1. คลาสแม่ของช่องทางการชำระเงิน
class PaymentChannel:
    def __init__(self, channel_type: str):
        self._channel_type = channel_type

    def get_channel_type(self) -> str:
        return self._channel_type

# 2. คลาสลูก: จ่ายด้วย QR Code
class QRPayment(PaymentChannel):
    def __init__(self):
        super().__init__("QR")

    def generate_qr_code(self, amount: float) -> str:
        return f"QR_IMG_DATA_FOR_{amount}_THB"

# 3. คลาสลูก: จ่ายด้วยเงินสด
class CashPayment(PaymentChannel):
    def __init__(self, received_amount: float):
        super().__init__("CASH")
        self.__received_amount = received_amount

    def calculate_change(self, total_amount: float) -> float:
        if self.__received_amount < total_amount:
            raise ValueError("จำนวนเงินไม่เพียงพอ")
        return self.__received_amount - total_amount


# 4. คลาส Payment หลัก
class Payment:
    def __init__(self, order: OnsiteOrder, payment_channel: PaymentChannel, amount: float):
        self.__order = order
        self.__payment_channel = payment_channel
        self.__amount = amount
        self.__status = "Pending"  # สถานะเริ่มต้น
        self.__timestamps = datetime.now()

    def set_status(self, status: str):
        self.__status = status
        # ถ้าจ่ายเงินสำเร็จ ให้อัปเดตสถานะที่ Order ทันที
        if status == "Success":
            self.__order.set_paid_status(True)

    def get_status(self) -> str:
        return self.__status


class ShopController:
    def __init__(self):
        self.__member = [] 
        self.__product = []
        self.__barista = []
        self.__current_guest = Customer() 

    def get_member(self, phone_number: str):
        for member in self.__member:
            if member.get_my_phone() == phone_number:
                return member
        return None
    
    def create_member(self, phone: str):
        self.__member.append(Member(phone))
        
    def add_product(self, product: Product):
        self.__product.append(product)

    def add_barista(self, barista: Barista):
        self.__barista.append(barista)

    def get_barista(self):
        return self.__barista

    def get_current_guest(self) -> Customer:
        return self.__current_guest
        
    def reset_current_guest(self):
        self.__current_guest = Customer()

    def create_order(self, customer: Customer, order_type: str) -> OnsiteOrder:
        return OnsiteOrder(customer, order_type)

    # --- [แก้ไข] อัปเดตให้รับ PaymentChannel และ amount ---
    def create_payment(self, order: OnsiteOrder, payment_channel: PaymentChannel, amount: float) -> Payment:
        return Payment(order, payment_channel, amount)


# ==========================================
# 3. Database Mock & Controller Init
# ==========================================
shop_bang_korn_67 = ShopController()
shop_bang_korn_67.add_barista(Barista("EMP-001", "John (Barista 1)"))

coke = Product("DR-001", "Coke", 20, 100)
coffee = Product("CF-001", "Iced Latte", 65, 100)
beer = Product("ALC-001", "Chang", 60, 50)
shop_bang_korn_67.add_product(coke)
shop_bang_korn_67.add_product(coffee)
shop_bang_korn_67.add_product(beer)

shop_bang_korn_67.create_member("0915919569")
member_mock = shop_bang_korn_67.get_member("0915919569")
member_mock.add_to_basket(coke.create_order_item(2)) 
member_mock.add_to_basket(beer.create_order_item(3))

guest_mock = shop_bang_korn_67.get_current_guest()
guest_mock.add_to_basket(coffee.create_order_item(1))



# ==========================================
# 4. Web / ShopController (API Endpoint)
# ==========================================
@app.post("/api/shopping/checkout-onsite")
def checkout_onsite(request: CheckoutRequest):
    """
    Phase 3: Checkout & Payment
    """
    if request.phone_number:
        customer_obj = shop_bang_korn_67.get_member(request.phone_number)
        if not customer_obj:
            raise HTTPException(status_code=400, detail="Member Not Found")
    else:
        customer_obj = shop_bang_korn_67.get_current_guest()

    basket = customer_obj.get_basket()
    items = basket.get_basket_items()
    if not items:
        raise HTTPException(status_code=400, detail="ตะกร้าสินค้าว่างเปล่า (กรุณาเลือกสินค้าก่อน)")

    for item in items:
        product = item.get_product_order_item()
        if product.validate_alcohol():
            if not product.validate_sale_time(datetime.now()):
                raise HTTPException(status_code=403, detail="มีแอลกอฮอล์ในตะกร้า: ขายได้เฉพาะ 11-14, 17-24 น.")

    drink_count = basket.count_drink_items()
    if drink_count > 10:
        raise HTTPException(status_code=400, detail="สั่งเครื่องดื่มได้สูงสุด 10 แก้ว/ออเดอร์")

    assigned_barista = None
    if drink_count > 0:
        baristas = shop_bang_korn_67.get_barista()
        for barista in baristas:
            if barista.can_accept_order(drink_count):
                assigned_barista = barista
                break
                
        if not assigned_barista:
            raise HTTPException(status_code=503, detail="คิวบาริสต้าเต็ม กรุณารอสักครู่")

    new_order = shop_bang_korn_67.create_order(customer_obj, "ONSITE")
    total_price = new_order.calculate_total()

    payment_response = {}

    # --- [แก้ไข] กระบวนการเลือก PaymentChannel ---
    if request.payment_channel.upper() == "QR":
        # สร้าง Channel
        channel = QRPayment()
        # สร้าง Payment Record
        payment = shop_bang_korn_67.create_payment(new_order, channel, total_price)
        
        qr_data = channel.generate_qr_code(total_price)
        payment_response = {"qr_code_image_data": qr_data, "instruction": "แสกน QR Code เพื่อชำระเงิน"}
        
        # ถือว่าสแกนจ่ายสำเร็จ
        payment.set_status("Success") 

    elif request.payment_channel.upper() == "CASH":
        channel = CashPayment(request.received_amount)
        payment = shop_bang_korn_67.create_payment(new_order, channel, total_price)
        
        try:
            change = channel.calculate_change(total_price)
            payment_response = {"received": request.received_amount, "change": change, "instruction": "รับเงินทอน"}
            payment.set_status("Success")
        except ValueError as e:
            payment.set_status("Failed")
            raise HTTPException(status_code=400, detail=str(e))
    else:
         raise HTTPException(status_code=400, detail="ช่องทางการชำระเงินไม่ถูกต้อง")

    # ตรวจสอบสถานะการจ่ายจากออเดอร์ (ซึ่ง Payment.set_status เข้าไปอัปเดตให้แล้ว)
    if new_order.check_payment_status():
        
        if assigned_barista:
            assigned_barista.assign_drinks(items)

        response_data = {
            "status": "Payment Success",
            "total_price": total_price,
            "payment_details": payment_response
        }

        if isinstance(customer_obj, Member):
            earned_points = new_order.calculate_member_point()
            customer_obj.received_point(earned_points)
            customer_obj.clear_basket() 
            
            response_data["member_status"] = "Member"
            response_data["earned_points"] = earned_points
            response_data["total_member_points"] = customer_obj.get_point()
        else:
            shop_bang_korn_67.reset_current_guest()
            response_data["member_status"] = "Guest"

        return response_data
    else:
        raise HTTPException(status_code=402, detail="Payment Failed")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)