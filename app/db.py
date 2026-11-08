from pymongo import MongoClient

from app.configuration import settings

_client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
_db = _client[settings.MONGODB_DATABASE]


def get_latest_model(user_id: str):
    return _db["cpep_models"].find_one(
        {"userId": user_id}, sort=[("versionNumber", -1)]
    )