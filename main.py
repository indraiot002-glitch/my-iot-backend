from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💾 તમારા બધા સાઇટના ડેટા અહીં સ્ટોર થશે
live_data = {
    "Demo_Site_1": {"status": "Offline", "last_update": "Never"},
    "Demo_Site_2": {"status": "Offline", "last_update": "Never"},
    "Demo_Site_3": {"status": "Offline", "last_update": "Never"},
}

alerts_log = []

class DevicePayload(BaseModel):
    site_name: str
    temperature: float = 0.0
    humidity: float = 0.0
    gas: int = 0
    door: str = "CLOSED"
    power: str = "ON"

@app.post("/api/device/update")
def update_data(data: DevicePayload):
    current_time = datetime.now().strftime("%I:%M %p")
    site = data.site_name

    if site not in live_data:
        live_data[site] = {}
        
    live_data[site]["status"] = "Online"
    live_data[site]["last_update"] = current_time

    # 🚨 એલાર્મ ચેક લોજિક
    if data.temperature >= 38.0:
        alerts_log.insert(0, {"site": site, "message": f"🚨 HIGH TEMP ALERT! Temp: {data.temperature}°C", "time": current_time})
    
    if data.gas > 600:
        alerts_log.insert(0, {"site": site, "message": f"🚨 FIRE/SMOKE ALERT! MQ2: {data.gas}", "time": current_time})

    if data.power.upper() == "FAIL":
        alerts_log.insert(0, {"site": site, "message": f"🚨 POWER FAILURE DETECTED!", "time": current_time})

    if data.door.upper() in ["OPEN", "OPN"]:
        alerts_log.insert(0, {"site": site, "message": f"🚨 SECURITY: Door Opened!", "time": current_time})

    # જો બધું ઓકે હોય તો સેફ મેસેજ
    if data.temperature < 38.0 and data.gas <= 600 and data.power.upper() == "ON" and data.door.upper() == "CLOSED":
        if not alerts_log or alerts_log[0]["site"] != site or "✅" not in alerts_log[0]["message"]:
            alerts_log.insert(0, {"site": site, "message": "✅ System Normal", "time": current_time})

    if len(alerts_log) > 30:
        alerts_log.pop()

    return {"status": "success"}

# 🔗 આ સાચો એન્ડપોઇન્ટ છે જે ફ્લટર એપ માંગે છે
@app.get("/api/devices/list")
def get_devices():
    return live_data

@app.get("/api/devices/alerts")
def get_alerts():
    return alerts_log
