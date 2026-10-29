import os
import secrets
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import urllib.request
import urllib.error
import json

load_dotenv("Backend/.env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
    if not mongo_uri:
        print("[ERROR] Neither MONGODB_URI nor MONGO_URI is set in environment.")
        return

    client = AsyncIOMotorClient(mongo_uri)
    db_name = os.getenv("MONGODB_DB", "restockiq")
    db = client[db_name]

    print("[1] Querying for admin@test.com in database...")
    user = await db.users.find_one({"email": "admin@test.com"})
    
    if not user:
        print("[INFO] admin@test.com does not exist in the database.")
    else:
        user_id = user["_id"]
        print(f"[FOUND] admin@test.com exists (User ID: {user_id})")
        
        # Check references
        item_count = await db.items.count_documents({"owner_id": user_id})
        print(f"[CHECK] Items referencing this user ID: {item_count}")
        
        if item_count > 0:
            print("[ACTION] Items reference this user. Disabling account and resetting password to a cryptographically secure random string...")
            random_pw = secrets.token_urlsafe(32)
            random_hash = pwd_context.hash(random_pw)
            await db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "disabled": True,
                    "password_hash": random_hash,
                    "status": "disabled",
                    "notes": "Demo user disabled for security"
                }}
            )
            print("[SUCCESS] Account disabled and password reset to unguessable random hash.")
        else:
            print("[ACTION] No items reference this user. Deleting admin@test.com from database...")
            await db.users.delete_one({"_id": user_id})
            print("[SUCCESS] admin@test.com deleted from database.")

    # Now verify login failure against live Render URL
    render_url = "https://restockiq-backend.onrender.com/api/v1/auth/login"
    print(f"\n[2] Probing live Render endpoint: POST {render_url}")
    probe_pw = os.getenv("DEMO_PROBE_PASSWORD", "audit-probe-pw-999")
    payload = json.dumps({"email": "admin@test.com", "password": probe_pw}).encode("utf-8")
    req = urllib.request.Request(
        render_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "RestockIQ-Audit/1.0"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[FAIL] Login unexpectedly succeeded with status code: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"[VERIFIED] Login failed as expected.")
        print(f"  HTTP Status Code: {e.code}")
        print(f"  Response Body:    {body}")
    except Exception as e:
        print(f"[ERROR] Could not complete HTTP request to Render: {e}")

if __name__ == "__main__":
    asyncio.run(main())
