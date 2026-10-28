import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()
uri = os.getenv("MONGO_URI")

if not uri:
    print("❌ Error: MONGO_URI not found in .env file.")
    exit(1)

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("[SUCCESS] Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("[ERROR] Connection failed:")
    print(e)
