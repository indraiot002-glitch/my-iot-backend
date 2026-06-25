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

# ૩ ફિક્સ ડિવાઇસ લિસ્ટ
live_data = {
    "GJ/AMD/BOPAL-512": {"status": "Offline", "last_update": "Never"},
    "GJ/AMD/BOPAL-513": {"status": "Offline", "last_update": "Never"},
    "GJ/AMD/BOPAL-514": {"status": "Offline", "last_update": "Never"},
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

    # સ્ટેટસ ચેક કન્ડિશન
    temp_status = "✅ Temperature Normal" if data.temperature < 38.0 else "🚨 Temperature Sensor Fail"
    humidity_status = "✅ Humidity Normal" if data.humidity < 70.0 else "🚨 High Humidity Alert"
    power_status = "✅ Power Normal" if data.power.upper() == "ON" else "🚨 Power Failure Alert"
    fire_status = "Not Found" if data.gas <= 600 else "🔥 DETECTED!"

    # 📱 image_311faf.png પ્રમાણે આખું મોટું સ્ટેટસ બોક્સ ફોર્મેટ
    status_block = (
        f"📋 {site} Current Status\n\n"
        f"🌡️ Temp: {data.temperature} C\n"
        f"💧 Humidity: {data.humidity} %\n"
        f"⚡ Power: {data.power}\n"
        f"🚪 Door: {data.door}\n"
        f"🔥 Fire: {fire_status}\n\n"
        f"{temp_status}\n"
        f"{humidity_status}\n"
        f"{power_status}"
    )

    # જો સિસ્ટમ ક્રિટિકલ મોડમાં હોય તો પહેલા સિંગલ એલાર્મ લાઇન પણ નાખવી
    if data.temperature >= 38.0:
        alerts_log.insert(0, {"site": site, "message": f"🚨🌡️ {site} Temperature Sensor Fail", "time": current_time})
    
    if data.power.upper() == "FAIL":
        alerts_log.insert(0, {"site": site, "message": f"🔄 {site} System Restarted", "time": current_time})

    # છેલ્લે આખું સ્ટેટસ કાર્ડ લિસ્ટમાં ઉમેરવું
    alerts_log.insert(0, {"site": site, "message": status_block, "time": current_time})

    if len(alerts_log) > 30:
        alerts_log.pop()

    return {"status": "success"}

@app.get("/api/devices/list")
def get_devices():
    return live_data

@app.get("/api/devices/alerts")
def get_alerts():
    return alerts_log
