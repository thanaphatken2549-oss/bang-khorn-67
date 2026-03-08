# notification.py
from abc import ABC, abstractmethod
from datetime import datetime


# ==========================================
# Abstract Base
# ==========================================
class Notification(ABC):
    """Abstract base class สำหรับระบบแจ้งเตือนทุกประเภท"""

    @abstractmethod
    def send(self, message: str) -> str:
        pass


# ==========================================
# 📱 SMS — แจ้งเตือนลูกค้า
# ==========================================
class SMSNotification(Notification):
    """ส่ง SMS แจ้งลูกค้าโดยตรง (ต้องระบุเบอร์โทร)"""

    def __init__(self, phone_number: str):
        self.__phone_number = phone_number
        self.__logs = []

    def send(self, message: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] 📱 SMS → {self.__phone_number}\n"
            f"   ข้อความ: {message}"
        )
        self.__logs.append(log_entry)
        print(log_entry)  # จำลองการส่ง SMS
        return "success"

    def get_phone(self) -> str:
        return self.__phone_number

    def get_logs(self) -> list:
        return self.__logs


# ==========================================
# 🖥️ System — แจ้งเตือนภายในระบบ (Staff/Admin)
# ==========================================
class SystemNotification(Notification):
    """แจ้งเตือนภายในระบบให้พนักงาน/ผู้ดูแล เห็นบน Dashboard"""

    def __init__(self):
        self.__logs = []

    def send(self, message: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] 🖥️ SYSTEM_ALERT: {message}"
        self.__logs.append(log_entry)
        print(log_entry)  # จำลองการแจ้งเตือนในระบบ
        return "success"

    def get_logs(self) -> list:
        return self.__logs
