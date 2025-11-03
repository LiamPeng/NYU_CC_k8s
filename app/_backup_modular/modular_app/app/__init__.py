# app/app/__init__.py
from flask import Flask, jsonify
from dotenv import load_dotenv
from .config import settings
from .routes_health import bp as health_bp
from .routes_todos import bp as todos_bp

def create_app() -> Flask:
    load_dotenv()  # 讀取本機 .env（K8s/Compose 會用環境變數覆蓋）
    app = Flask(__name__)

    # JSON 錯誤處理（簡單版）
    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="internal error"), 500

    app.register_blueprint(health_bp)
    app.register_blueprint(todos_bp)

    @app.get("/")
    def root():
        return jsonify(app="hw2-todo", status="ok"), 200

    return app
