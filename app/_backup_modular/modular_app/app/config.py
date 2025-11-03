import os

class Settings:
    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")
    PORT: int = int(os.getenv("PORT", "5000"))
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://mongo:27017/todos_db")  # K8s/Compose 預設

settings = Settings()
