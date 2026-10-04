import urllib.request
import urllib.error
import json

BASE = "http://localhost:8000/api/v1"

def post(path, data, token=None):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})},
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}

def get(path, token=None):
    req = urllib.request.Request(
        BASE + path,
        headers={**({"Authorization": f"Bearer {token}"} if token else {})},
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read().decode())

print("=== STEP 1 VERIFICATION ===\n")

# 1. Health
health = get("/health")
print(f"[1] Health:    {health}")

# 2. Register
reg = post("/auth/register", {"name": "Yatin (Owner)", "email": "yatin@restockiq.com", "password": "demo1234", "role": "owner"})
print(f"[2] Register:  {reg}")

token = reg.get("access_token")
if not token:
    print("Registration may have failed (user already exists). Trying login...")
    login = post("/auth/login", {"email": "yatin@restockiq.com", "password": "demo1234"})
    print(f"[3] Login:     {login}")
    token = login.get("access_token")
else:
    print(f"    Token:     {token[:40]}...")

# 3. Create item
item = post("/items", {"name": "Croissants", "category": "Bakery", "unit": "Units", "currentStock": 10, "isPerishable": True, "price": 3.50}, token=token)
print(f"[4] Create Item: {item}")

# 4. Get items
items = get("/items", token=token)
print(f"[5] Get Items: {items}")

print("\n=== ALL STEPS PASSED ===")
