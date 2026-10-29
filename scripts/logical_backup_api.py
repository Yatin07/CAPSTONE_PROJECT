import os
import json
import requests
from pathlib import Path
from dotenv import dotenv_values

root_dir = Path(__file__).resolve().parent.parent
creds_file = root_dir / ".live_credentials.local"
if not creds_file.exists():
    print(f"ERROR: {creds_file} not found")
    exit(1)

creds = dotenv_values(creds_file)
base_url = "https://restockiq-backend.onrender.com"

# 1. Login
login_resp = requests.post(f"{base_url}/api/v1/auth/login", json={
    "email": creds["EMAIL"],
    "password": creds["PASSWORD"]
})
if login_resp.status_code != 200:
    print(f"ERROR: Login failed with status {login_resp.status_code}: {login_resp.text}")
    exit(1)

token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

backup_dir = root_dir / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)

# 2. Fetch Items
items_resp = requests.get(f"{base_url}/api/v1/items", headers=headers)
items_data = items_resp.json()
with open(backup_dir / "api_items_demo_manager.json", "w", encoding="utf-8") as f:
    json.dump(items_data, f, indent=2)
print(f"Exported items: {len(items_data.get('items', []))} items to backups/api_items_demo_manager.json")

# 3. Fetch Forecasts Today
forecasts_resp = requests.get(f"{base_url}/api/v1/forecasts/today", headers=headers)
forecasts_data = forecasts_resp.json()
with open(backup_dir / "api_forecasts_today_demo_manager.json", "w", encoding="utf-8") as f:
    json.dump(forecasts_data, f, indent=2)
print(f"Exported forecasts today: {len(forecasts_data.get('items', []))} items to backups/api_forecasts_today_demo_manager.json")

# 4. Fetch Waste Alerts
alerts_resp = requests.get(f"{base_url}/api/v1/waste-alerts", headers=headers)
alerts_data = alerts_resp.json()
with open(backup_dir / "api_waste_alerts_demo_manager.json", "w", encoding="utf-8") as f:
    json.dump(alerts_data, f, indent=2)
print(f"Exported waste alerts: {len(alerts_data.get('alerts', []))} alerts to backups/api_waste_alerts_demo_manager.json")
print("API logical backup completed successfully.")
