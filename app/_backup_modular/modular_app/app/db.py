from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from .config import settings

_client = None
_db = None
_todos = None

def get_client():
    global _client, _db, _todos
    if _client is None:
        # 2 秒連線測試 timeout，避免 readiness 掛太久
        _client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        _db = _client.get_default_database() or _client.get_database("todos_db")
        _todos = _db.get_collection("todos")
        _todos.create_index("done")
    return _client

def get_collection():
    if _todos is None:
        get_client()
    return _todos

def ping_db() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        return False
