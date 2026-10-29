import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pymongo
from bson import json_util

# Load Backend/.env
env_path = Path(__file__).resolve().parent.parent / "Backend" / ".env"
load_dotenv(dotenv_path=env_path)

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print("ERROR: MONGO_URI is not set in Backend/.env", file=sys.stderr)
    sys.exit(1)

db_name = os.getenv("MONGODB_DB", "restockiq")
backup_dir = Path(__file__).resolve().parent.parent / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)

collections_to_backup = ["users", "items", "forecasts", "intraday_sales"]

try:
    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    # Ping to check connectivity
    client.admin.command('ping')
except Exception as e:
    print(f"ATLAS UNREACHABLE: Failed to connect to MongoDB: {type(e).__name__}")
    sys.exit(2)

db = client[db_name]
print(f"Connected to database: {db_name}")

results = {}
for coll_name in collections_to_backup:
    try:
        coll = db[coll_name]
        docs = list(coll.find({}))
        out_file = backup_dir / f"{coll_name}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(json_util.dumps(docs, indent=2))
        results[coll_name] = len(docs)
        print(f"Collection '{coll_name}': {len(docs)} documents exported to backups/{coll_name}.json")
    except Exception as e:
        print(f"ERROR exporting '{coll_name}': {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)

print("Export completed successfully.")
