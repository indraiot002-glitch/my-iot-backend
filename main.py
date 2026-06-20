from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔐 ક્રોમ બ્રાઉઝરની CORS એરર સોલ્વ કરવા માટેની સિક્યોરિટી પરવાનગી
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💾 સર્વરની મેમરીમાં ૪ ડેમો સાઇટ્સનો લાઇવ ડેટા સ્ટોર કરવા માટે
live_data = {
    "Demo_Site_1": {"temperature": 33.6, "humidity": 55.0, "gas": 4, "door": "OPEN", "power": "ON", "is_alarm": True},
    "Demo_Site_2": {"temperature": 26.5, "humidity": 45.0, "gas": 0, "door": "CLOSED", "power": "ON", "is_alarm": False},
    "Demo_Site_3": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
    "Demo_Site_4": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
}

# ડેમો યુઝર્સ અને તેમને અસાઇન કરેલી સાઇટ્સ
users_db = {
    "user1": {"password": "123", "sites": ["Demo_Site_1", "Demo_Site_2"]},
    "user2": {"password": "456", "sites": ["Demo_Site_3", "Demo_Site_4"]}
}

# 📡 હાર્ડવેર (ESP32/Arduino) માંથી આવતા લાઇવ ડેટાનું મોડેલ (Payload)
class DevicePayload(BaseModel):
    site_name: str
    temperature: float
    humidity: float  # લાઈવ ભેજનો ડેટા
    gas: int
    door: str
    power: str = "ON" # લાઈવ પાવરનો ડેટા

# ૧. મોબાઇલ એપ લોગિન માટેની API
@app.post("/api/login")
def login(data: dict):
    username = data.get("username")
    password = data.get("password")
    if username in users_db and users_db[username]["password"] == password:
        return {"status": "success", "sites": users_db[username]["sites"]}
    return {"status": "error", "message": "Invalid Login"}

# ૨. હાર્ડવેર માંથી લાઇવ ડેટા સ્વીકારવા માટેની API
@app.post("/api/device/update")
def update_data(data: DevicePayload):
    if data.site_name in live_data:
        live_data[data.site_name] = {
            "temperature": data.temperature,
            "humidity": data.humidity,
            "gas": data.gas,
            "door": data.door.upper(),
            "power": data.power.upper(),
            "is_alarm": data.gas > 500 or data.door.upper() == "OPEN"
        }
        return {"status": "updated"}
    return {"status": "site_not_found"}

# ૩. મોબાઇલ એપ પર એલાર્મ અને ડેટા મોકલવા માટેની API (POST)
@app.post("/api/app/get-alarms")
def get_alarms(data: dict):
    user_sites = data.get("sites", [])
    response_data = {}
    for site in user_sites:
        if site in live_data:
            response_data[site] = live_data[site]
    return {"my_sites_data": response_data}

# ૪. ఫ્લટર વેબ એપ માટે બધી જ સાઇટ્સનો લાઈવ ડેટા મોકલતી નવી API (GET)
@app.get("/api/devices/status")
def get_device_status():
    return live_data
