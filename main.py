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

# 💾 સર્વરની શરુઆતની મેમરીમાં ૪ ડેમો સાઇટ્સનો ડેટા (હાર્ડવેર કનેક્ટ થતાં જ આ બદલાઈ જશે)
live_data = {
    "Demo_Site_1": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
    "Demo_Site_2": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
    "Demo_Site_3": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
    "Demo_Site_4": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
}

# 📡 ફિઝિકલ હાર્ડવેર માંથી આવતા લાઇવ ડેટાનું સેફ મોડેલ
class DevicePayload(BaseModel):
    site_name: str
    temperature: float
    humidity: float = 0.0  # 👈 જો હાર્ડવેર હ્યુમિડિટી ન મોકલે તો એરર નહીં આવે, ડિફોલ્ટ 0.0 લેશે
    gas: int
    door: str
    power: str = "ON"      # 👈 જો હાર્ડવેર પાવર ન મોકલે તો ડિફોલ્ટ ON રહેશે

# ૧. હાર્ડવેર (ESP32/Python) માંથી લાઇવ ડેટા સ્વીકારવા માટેની API
@app.post("/api/device/update")
def update_data(data: DevicePayload):
    if data.site_name in live_data:
        live_data[data.site_name] = {
            "temperature": data.temperature,
            "humidity": data.humidity,
            "gas": data.gas,
            "door": data.door.upper(),   # અક્ષરો મોટા કરવા માટે (e.g., CLOSR, CLOSED)
            "power": data.power.upper(), # અક્ષરો મોટા કરવા માટે (e.g., FAIL, OFF)
            "is_alarm": data.gas > 500 or data.door.upper() in ["OPEN", "OPN"]
        }
        return {"status": "updated"}
    return {"status": "site_not_found"}

# ૨. ફ્લટર ડેશબોર્ડ એપ માટે બધી જ સાઇટ્સનો લાઈવ ડેટા મોકલતી API
@app.get("/api/devices/status")
def get_device_status():
    return live_data
