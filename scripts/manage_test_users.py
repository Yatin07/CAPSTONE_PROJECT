import os
import sys
from pathlib import Path
from pymongo import MongoClient

def inspect_and_disable_test_users():
    env_path = Path("Backend/.env")
    if not env_path.exists():
        print("[ERROR] Backend/.env not found.")
        sys.exit(1)

    uri = None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("MONGODB_URI=") or line.startswith("MONGO_URI="):
                uri = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

    if not uri:
        print("[ERROR] MONGODB_URI not found in Backend/.env")
        sys.exit(1)

    # Connect to MongoDB
    client = MongoClient(uri)
    db_name = os.getenv("MONGODB_DB", "restockiq")
    db = client[db_name]
    users_coll = db.users

    print("=" * 70)
    print("           RESTOCKIQ: USER DATABASE AUDIT & HARDENING            ")
    print("=" * 70)

    # Find all users - STRICTLY project only safe fields: email, disabled, role, createdAt
    users = list(users_coll.find({}, {"email": 1, "disabled": 1, "role": 1, "createdAt": 1, "_id": 1}))

    print(f"Total Users Found in Database: {len(users)}\n")
    print(f"{'Email':<35} | {'Role':<10} | {'Disabled':<10} | {'Action Taken'}")
    print("-" * 75)

    test_patterns = ["test", "demo", "sample", "admin@test.com", "example.com", "admin@admin.com", "manager@cafe.com"]

    for u in users:
        email = u.get("email", "<no-email>")
        role = u.get("role", "user")
        is_disabled = u.get("disabled", False)

        # Identify if user is a seeded/test user
        is_test_account = any(pattern in email.lower() for pattern in test_patterns)

        action = "None (Active user)"
        if is_disabled:
            action = "Already Disabled"
        elif is_test_account:
            # Disable test account
            users_coll.update_one({"_id": u["_id"]}, {"$set": {"disabled": True}})
            action = "DISABLED (Test account)"
            is_disabled = True

        print(f"{email:<35} | {str(role):<10} | {str(is_disabled):<10} | {action}")

    print("\n" + "=" * 70)
    print("  [SUCCESS] All seeded and test accounts audited and disabled.")
    print("=" * 70)

if __name__ == "__main__":
    inspect_and_disable_test_users()
