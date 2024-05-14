from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

mongo_uri = f"mongodb+srv://asingh:{os.environ['MONGODB_PWD']}@cluster0.onndt4w.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)

db = client.db_blinkit
