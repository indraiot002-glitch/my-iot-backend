from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- In-memory stores ----------
# Device online/offline status (for list view)
live_status = {
    "GJ/AMD/BOPAL-512": {"status": "Offline", "last_update": "Never"},
    "GJ/AMD/BOPAL-513": {"status": "Offline", "last_update": "Never"},
    "GJ/AMD/BOPAL-514": {"status": "Offline", "last_update": "Never"},
}

# Full latest data per device (to serve to Flutter app)
latest_data = {}

# Alerts log (for notification history)
alerts_log = []

# ---------- Request model ----------
class DevicePayload(BaseModel):
    site_name: str
    temperature: float = 0.0
    humidity: float = 0.0
    gas: int = 0
    door: str = "CLOSED"
    power: str = "ON"

# ---------- POST endpoint ----------
@app.post("/api/device/update")
def update_data(data: DevicePayload):
    current_time = datetime.now().strftime("%I:%M %p")
    site = data.site_name

    # Update live_status
    if site not in live_status:
        live_status[site] = {}
    live_status[site]["status"] = "Online"
    live_status[site]["last_update"] = current_time

    # Store full data (for GET /status)
    latest_data[site] = {
        "siteName": site,
        "temperature": data.temperature,
        "humidity": data.humidity,
        "mq2": data.gas,
        "doorState": 1 if data.door.upper() == "OPEN" else 0,
        "powerState": 1 if data.power.upper() == "FAIL" else 0,
        # We don't have thresholds in the payload, so we set placeholders (or you can store them)
        "tempHigh": 38.0,
        "tempLow": 34.0,
        "humHigh": 70.0,
        "humLow": 60.0,
        "alarms": {
            "tempHigh": data.temperature >= 38.0,
            "humHigh": data.humidity >= 70.0,
            "doorOpen": data.door.upper() == "OPEN",
            "powerFail": data.power.upper() == "FAIL",
            "smoke": data.gas >= 600,
            "dhtFail": False,  # not provided
        },
        "lastUpdated": current_time,
    }

    # Build the status block (as you already do)
    temp_status = "✅ Temperature Normal" if data.temperature < 38.0 else "🚨 Temperature Sensor Fail"
    humidity_status = "✅ Humidity Normal" if data.humidity < 70.0 else "🚨 High Humidity Alert"
    power_status = "✅ Power Normal" if data.power.upper() == "ON" else "🚨 Power Failure Alert"
    fire_status = "Not Found" if data.gas <= 600 else "🔥 DETECTED!"

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

    # Add individual alerts
    if data.temperature >= 38.0:
        alerts_log.insert(0, {"site": site, "message": f"🚨🌡️ {site} Temperature Sensor Fail", "time": current_time})
    if data.power.upper() == "FAIL":
        alerts_log.insert(0, {"site": site, "message": f"🔄 {site} System Restarted", "time": current_time})
    # Always add the full status block as the latest message
    alerts_log.insert(0, {"site": site, "message": status_block, "time": current_time})

    # Keep log size manageable
    if len(alerts_log) > 30:
        alerts_log.pop()

    return {"status": "success"}

# ---------- GET endpoints ----------
@app.get("/api/devices/list")
def get_devices():
    return live_status

@app.get("/api/devices/alerts")
def get_alerts():
    return alerts_log

# NEW: Get latest data for a specific device (for Flutter app)
@app.get("/api/device/status/{site_name}")
def get_device_status(site_name: str):
    if site_name not in latest_data:
        raise HTTPException(status_code=404, detail="Device not found or no data yet")
    return latest_data[site_name]

# NEW: Optionally get all devices' latest data
@app.get("/api/devices/all")
def get_all_devices():
    return latest_data

