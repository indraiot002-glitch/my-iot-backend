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

# 💾 ભાવિનભાઈના ફિક્સ ૩ ડિવાઇસનું લાઇવ સ્ટેટસ
live_data = {
    "GJ/AMD/BOPAL-512": {"status": "Online", "last_update": "Never"},
    "GJ/AMD/BOPAL-513": {"status": "Offline", "last_update": "Never"},
    "GJ/AMD/BOPAL-514": {"status": "Offline", "last_update": "Never"},
}

# 💬 એલાર્મ મેસેજ લોગ
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

    # જો નવું સાઇટ નામ હોય તો લિસ્ટમાં જોડી દેવું
    if site not in live_data:
        live_data[site] = {}
        
    live_data[site]["status"] = "Online"
    live_data[site]["last_update"] = current_time

    # 🚨 ૧. તાપમાન એલાર્મ ચેક
    if data.temperature >= 38.0:
        alerts_log.insert(0, {"site": site, "message": f"🚨 HIGH TEMP ALERT! Temp: {data.temperature}°C", "time": current_time, "is_critical": True})
    
    # 🚨 ૨. ગેસ લીકેજ એલાર્મ ચેક
    if data.gas > 600:
        alerts_log.insert(0, {"site": site, "message": f"🚨 FIRE/SMOKE ALERT! MQ2 Value: {data.gas}", "time": current_time, "is_critical": True})

    # 🚨 ૩. પાવર ફેલ એલાર્મ ચેક
    if data.power.upper() == "FAIL":
        alerts_log.insert(0, {"site": site, "message": f"🚨 POWER FAILURE DETECTED!", "time": current_time, "is_critical": True})

    # 🔓 ૪. દરવાજો ખુલ્લો એલાર્મ ચેક
    if data.door.upper() in ["OPEN", "OPN"]:
        alerts_log.insert(0, {"site": site, "message": f"🚨 SECURITY: Door Opened!", "time": current_time, "is_critical": True})

    # જો બધું નોર્મલ હોય તો સાદો સક્સેસ મેસેજ (આમાં 🚨 નથી)
    if data.temperature < 38.0 and data.gas <= 600 and data.power.upper() == "ON" and data.door.upper() == "CLOSED":
        # ફક્ત છેલ્લો મેસેજ એલાર્મ વગરનો હોય તો જ ઉમેરવો જેથી પૂર ન આવે
        if not alerts_log or alerts_log[0]["site"] != site or "✅" not in alerts_log[0]["message"]:
            alerts_log.insert(0, {"site": site, "message": "✅ System Normal", "time": current_time, "is_critical": False})

    if len(alerts_log) > 30:
        alerts_log.pop()

    return {"status": "processed"}

@app.get("/api/devices/list")
def get_devices():
    return live_data

@app.get("/api/devices/alerts")
def get_alerts():
    return alerts_log
