# ใช้ Python 3.11 เป็น Base Image (เสถียรและน้ำหนักเบา)
FROM python:3.11-slim

# ตั้งค่า Working Directory ใน Container
WORKDIR /app

# ก๊อปปี้ไฟล์ requirement.txt ไปติดตั้งก่อน
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# ก๊อปปี้โค้ด Python ทั้งหมดของเราเข้าไปใน Container
COPY . .

# คำสั่งรันโปรแกรมเมื่อ Container เริ่มทำงาน
CMD ["python", "project.py"]