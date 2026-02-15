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

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...), 
    description: str = Form(...),
    machine_id: str = Form(...)
):
    # บรรทัดเหล่านี้ต้องมีย่อหน้าเข้าไป 4 ช่อง (1 Tab)
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # ส่วนนี้ต้องอยู่ระดับเดียวกับ file_location เพื่อให้อยู่ในฟังก์ชันเดียวกัน
    image_data = {
        "machine_id": machine_id,
        "filename": file.filename,
        "description": description,
        "url": f"https://machine-backend-ay9v.onrender.com/images/{file.filename}" 
    }
    
    # บันทึกลง MongoDB และส่งผลลัพธ์กลับ
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

# อย่าลืมเพิ่มฟังก์ชันนี้สำหรับแท็บ Database Records ที่เราทำเพิ่มนะครับเพื่อน
@app.get("/get-all-machines")
async def get_all_machines():
    machines = []
    cursor = image_collection.find({})
    async for document in cursor:
        document["_id"] = str(document["_id"])
        machines.append(document)
    return machines

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
