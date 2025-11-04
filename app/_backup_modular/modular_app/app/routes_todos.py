# app/app/routes_todos.py
from flask import Blueprint, jsonify, request
from bson import ObjectId
from pymongo import ReturnDocument
from .db import get_collection

bp = Blueprint("todos", __name__, url_prefix="/api/todos")

def _to_dict(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc

@bp.get("/")
def list_todos():
    todos = list(get_collection().find({}).sort("_id", -1))
    return jsonify([_to_dict(t) for t in todos]), 200

@bp.post("/")
def create_todo():
    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    doc = {"title": title, "done": False}
    res = get_collection().insert_one(doc)
    doc["_id"] = res.inserted_id
    return jsonify(_to_dict(doc)), 201

@bp.patch("/<todo_id>")
def patch_todo(todo_id):
    try:
        _id = ObjectId(todo_id)
    except Exception:
        return jsonify(error="invalid id"), 400
    data = request.get_json(force=True, silent=True) or {}
    patch = {}
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify(error="title cannot be empty"), 400
        patch["title"] = title
    if "done" in data:
        patch["done"] = bool(data["done"])
    if not patch:
        return jsonify(error="no fields to update"), 400

    doc = get_collection().find_one_and_update(
        {"_id": _id},
        {"$set": patch},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        return jsonify(error="not found"), 404
    return jsonify(_to_dict(doc)), 200

@bp.delete("/<todo_id>")
def delete_todo(todo_id):
    try:
        _id = ObjectId(todo_id)
    except Exception:
        return jsonify(error="invalid id"), 400
    res = get_collection().delete_one({"_id": _id})
    if res.deleted_count == 0:
        return jsonify(error="not found"), 404
    return jsonify(ok=True), 200
