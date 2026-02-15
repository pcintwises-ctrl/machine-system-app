from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
import shutil
import os

app = FastAPI()

# เชื่อมต่อ MongoDB
MONGO_DETAILS = "mongodb+srv://phonlawat_api:kPOIUadGVRbjOM59@cluster0.bkogsh0.mongodb.net/?appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.factory_db
image_collection = database.get_collection("machine_data")

# ตั้งค่า CORS เพื่อให้หน้าเว็บ (Frontend) ติดต่อกับ Backend ได้
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# ตั้งค่าที่เก็บรูปภาพ
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...), 
    description: str = Form(...),
    machine_id: str = Form(...)
):
    # บันทึกไฟล์ลงในโฟลเดอร์ uploads
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # จัดการข้อมูลรูปภาพและที่อยู่ URL บน Render
    image_data = {
        "machine_id": machine_id,
        "filename": file.filename,
        "description": description,
        "url": f"https://machine-backend-ay9v.onrender.com/images/{file.filename}" 
    }
    
    # บันทึกลง MongoDB
    await image_collection.insert_one(image_data)
    return {"status": "Success", "message": "บันทึกข้อมูลเครื่องเรียบร้อย!"}

@app.get("/get-machine/{m_id}")
async def get_machine(m_id: str):
    # ค้นหาข้อมูลตามหมายเลขเครื่อง
    data = await image_collection.find_one({"machine_id": m_id})
    if data:
        data["_id"] = str(data["_id"])
        return data
    return {"error": "ไม่พบหมายเลขเครื่องนี้"}

# --- เพิ่มฟังก์ชันดึงข้อมูลทั้งหมดสำหรับแท็บ Database Records ---
@app.get("/get-all-machines")
async def get_all_machines():
    machines = []
    # ดึงข้อมูลทั้งหมดจาก Collection และแปลงข้อมูลให้อยู่ในรูปแบบที่ JSON เข้าใจได้
    cursor = image_collection.find({})
    async for document in cursor:
        document["_id"] = str(document["_id"])
        machines.append(document)
    return machines

if __name__ == "__main__":
    import uvicorn
    # รัน Server ที่ Port 8000 สำหรับการทดสอบ Local
    uvicorn.run(app, host="0.0.0.0", port=8000)
