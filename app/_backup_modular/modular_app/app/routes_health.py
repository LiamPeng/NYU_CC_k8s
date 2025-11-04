from flask import Blueprint, jsonify
from .db import ping_db

bp = Blueprint("health", __name__)

@bp.get("/healthz")   # livenessProbe：只要程序活著就回 200
def healthz():
    return jsonify(status="ok"), 200

@bp.get("/readyz")    # readinessProbe：確認依賴（Mongo）可用
def readyz():
    if ping_db():
        return jsonify(status="ready"), 200
    return jsonify(status="not-ready", reason="mongodb unreachable"), 503
