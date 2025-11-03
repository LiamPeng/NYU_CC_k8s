# app/wsgi.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    # 本機直跑（開發用）；Docker/K8s 會用 gunicorn 啟動
    from app.config import settings
    app.run(host="0.0.0.0", port=settings.PORT, debug=(settings.FLASK_ENV == "development"))
