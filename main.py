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

# 💾 લાઇવ સ્ટેટસ સ્ટોર કરવા માટે
live_data = {
    "Demo_Site_1": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
    "Demo_Site_2": {"temperature": 0.0, "humidity": 0.0, "gas": 0, "door": "CLOSED", "power": "OFF", "is_alarm": False},
}

# 💬 ચેટ સ્ક્રીન માટે એલાર્મ લોગ હિસ્ટ્રી (શરૂઆતમાં થોડો ડેમો ડેટા રાખ્યો છે)
alerts_log = [
    {"site": "Demo_Site_1", "message": "🚨 System Initialized Successfully", "time": "10:00 AM", "type": "info"},
]

class DevicePayload(BaseModel):
    site_name: str
    temperature: float
    humidity: float = 0.0
    gas: int
    door: str
    power: str = "ON"

@app.post("/api/device/update")
def update_data(data: DevicePayload):
    if data.site_name in live_data:
        old_door = live_data[data.site_name]["door"]
        old_power = live_data[data.site_name]["power"]
        
        # વર્તમાન સમય (IST ટાઈમ માટે એપ સાઇડ હેન્ડલ કરવું સારું, પણ અહીં સર્વર ટાઈમ ફોર્મેટ કર્યો છે)
        current_time = datetime.now().strftime("%I:%M %p")

        # 🚨 નવા એલાર્મ ચેક કરીને ચેટ હિસ્ટ્રીમાં ઉમેરવા
        if data.gas > 500:
            alerts_log.insert(0, {"site": data.site_name, "message": f"🔥 HIGH GAS DETECTED! Value: {data.gas}", "time": current_time, "type": "danger"})
        
        if data.door.upper() in ["OPEN", "OPN"] and old_door != "OPEN":
            alerts_log.insert(0, {"site": data.site_name, "message": "🔓 Security Alert: Door Opened!", "time": current_time, "type": "warning"})
        elif data.door.upper() in ["CLOSED", "CLSR"] and old_door == "OPEN":
            alerts_log.insert(0, {"site": data.site_name, "message": "🔒 Safe: Door Closed Now", "time": current_time, "type": "success"})

        if data.power.upper() == "FAIL" and old_power != "FAIL":
            alerts_log.insert(0, {"site": data.site_name, "message": "⚡ Power Failure Detected!", "time": current_time, "type": "danger"})
        elif data.power.upper() == "ON" and old_power == "FAIL":
            alerts_log.insert(0, {"site": data.site_name, "message": "🔋 Power Restored Successfully", "time": current_time, "type": "success"})

        # મેક્સિમમ ૫૦ ચેટ મેસેજ જ રાખવા જેથી સર્વર હેંગ ન થાય
        if len(alerts_log) > 50:
            alerts_log.pop()

        # લાઇવ ડેટા અપડેટ
        live_data[data.site_name] = {
            "temperature": data.temperature,
            "humidity": data.humidity,
            "gas": data.gas,
            "door": data.door.upper(),
            "power": data.power.upper(),
            "is_alarm": data.gas > 500 or data.door.upper() in ["OPEN", "OPN"]
        }
        return {"status": "updated"}
    return {"status": "site_not_found"}

@app.get("/api/devices/status")
def get_device_status():
    return live_data

# 💬 નવી ચેટ એલાર્મ API
@app.get("/api/devices/alerts")
def get_alerts_log():
    return alerts_log
