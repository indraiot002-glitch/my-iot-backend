from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# સર્વરની મેમરીમાં ૪ ડેમો સાઇટ્સનો લાઇવ ડેટા સ્ટોર કરવા માટે
live_data = {
    "Demo_Site_1": {"temperature": 0.0, "gas": 0, "door": "CLOSED", "is_alarm": False},
    "Demo_Site_2": {"temperature": 0.0, "gas": 0, "door": "CLOSED", "is_alarm": False},
    "Demo_Site_3": {"temperature": 0.0, "gas": 0, "door": "CLOSED", "is_alarm": False},
    "Demo_Site_4": {"temperature": 0.0, "gas": 0, "door": "CLOSED", "is_alarm": False},
}

# ડેમો યુઝર્સ અને તેમને અસાઇન કરેલી સાઇટ્સ
users_db = {
    "user1": {"password": "123", "sites": ["Demo_Site_1", "Demo_Site_2"]},
    "user2": {"password": "456", "sites": ["Demo_Site_3", "Demo_Site_4"]}
}

class DevicePayload(BaseModel):
    site_name: str
    temperature: float
    gas: int
    door: str

# ૧. એપ લોગિન માટેની API
@app.post("/api/login")
def login(data: dict):
    username = data.get("username")
    password = data.get("password")
    if username in users_db and users_db[username]["password"] == password:
        return {"status": "success", "sites": users_db[username]["sites"]}
    return {"status": "error", "message": "Invalid Login"}

# ૨. આર્દુઇનો માંથી ડેટા સ્વીકારવા માટેની API
@app.post("/api/device/update")
def update_data(data: DevicePayload):
    if data.site_name in live_data:
        live_data[data.site_name] = {
            "temperature": data.temperature,
            "gas": data.gas,
            "door": data.door,
            "is_alarm": data.gas > 500 or data.door == "OPEN" # ૫૦૦ થી વધુ ગેસ પર એલાર્મ
        }
        return {"status": "updated"}
    return {"status": "site_not_found"}

# ૩. મોબાઇલ એપ પર એલાર્મ અને ડેટા મોકલવા માટેની API
@app.post("/api/app/get-alarms")
def get_alarms(data: dict):
    user_sites = data.get("sites", [])
    response_data = {}
    for site in user_sites:
        if site in live_data:
            response_data[site] = live_data[site]
    return {"my_sites_data": response_data}