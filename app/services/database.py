from pymongo import MongoClient
from app.core.config import settings
import datetime

client = MongoClient(settings.COSMOS_MONGO_URI)
db = client[settings.DATABASE_NAME]
history_collection = db[settings.HISTORY_COLLECTION_NAME]

def save_user_query(question: str):
    """Saves user query to the history collection"""
    history_collection.insert_one({
        "question": question,
        "timestamp": datetime.datetime.utcnow()
    })

def retrieve_user_history(limit: int = 5) -> list[str]:
    """Retrieves the most recent user queries"""
    history = history_collection.find().sort("timestamp", -1).limit(limit)
    return [item["question"] for item in history]

