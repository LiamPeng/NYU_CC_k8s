import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from bson.objectid import ObjectId
from bson.errors import InvalidId

# ---------- 環境設定 ----------
load_dotenv()  # 讀取同層 .env
FLASK_ENV = os.getenv("FLASK_ENV", "production")
PORT = int(os.getenv("PORT", "5000"))

# 支援 MONGO_URI（優先），否則回退 MONGO_HOST / MONGO_PORT
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    mongodb_host = os.environ.get("MONGO_HOST", "localhost")
    mongodb_port = int(os.environ.get("MONGO_PORT", "27017"))
    MONGO_URI = f"mongodb://{mongodb_host}:{mongodb_port}/todos_db"

# ---------- 資料庫連線 ----------
# 縮短 serverSelectionTimeout，readiness 失敗能快回應
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
try:
   db = client.get_database("todos_db") 
except ConfigurationError:
    db = client.get_database("todos_db")

todos = db.get_collection("todo")
todos.create_index("done")

app = Flask(__name__)
title = "TODO with Flask"
heading = "ToDo Reminder"

def redirect_url():
    return request.args.get("next") or request.referrer or url_for("tasks")

# ---------- 健康檢查（K8s Probes 會用） ----------
@app.get("/healthz")  # liveness：只要程序活著即可
def healthz():
    return jsonify(status="ok"), 200

@app.get("/readyz")   # readiness：要能 ping 到 Mongo 才算就緒
def readyz():
    try:
        client.admin.command("ping")
        return jsonify(status="ready"), 200
    except ServerSelectionTimeoutError:
        return jsonify(status="not-ready", reason="mongodb unreachable"), 503

# ---------- 頁面 ----------
@app.route("/list")
def lists():
    # 顯示所有任務
    todos_l = list(todos.find({}).sort("_id", -1))
    a1 = "active"
    return render_template("index.html", a1=a1, todos=todos_l, t=title, h=heading)

@app.route("/")
@app.route("/uncompleted")
def tasks():
    # 顯示未完成
    todos_l = list(todos.find({"done": "no"}).sort("_id", -1))
    a2 = "active"
    return render_template("index.html", a2=a2, todos=todos_l, t=title, h=heading)

@app.route("/completed")
def completed():
    # 顯示已完成
    todos_l = list(todos.find({"done": "yes"}).sort("_id", -1))
    a3 = "active"
    return render_template("index.html", a3=a3, todos=todos_l, t=title, h=heading)

@app.route("/done")
def done():
    # 切換 done 狀態
    _id = request.values.get("_id")
    try:
        doc = todos.find_one({"_id": ObjectId(_id)})
    except Exception:
        return redirect(redirect_url())
    if doc:
        new_done = "no" if doc.get("done") == "yes" else "yes"
        todos.update_one({"_id": doc["_id"]}, {"$set": {"done": new_done}})
    return redirect(redirect_url())

@app.route("/action", methods=["POST"])
def action():
    # 新增任務
    name = (request.values.get("name") or "").strip()
    desc = (request.values.get("desc") or "").strip()
    date = (request.values.get("date") or "").strip()
    pr = (request.values.get("pr") or "").strip()
    if not name:
        return redirect("/list")  # 或回首頁並顯示錯誤
    todos.insert_one({"name": name, "desc": desc, "date": date, "pr": pr, "done": "no"})
    return redirect("/list")

@app.route("/remove")
def remove():
    # 刪除任務
    key = request.values.get("_id")
    try:
        todos.delete_one({"_id": ObjectId(key)})
    except Exception:
        pass
    return redirect("/")

@app.route("/update")
def update():
    # 進入更新頁
    _id = request.values.get("_id")
    try:
        doc = todos.find_one({"_id": ObjectId(_id)})
    except Exception:
        doc = None
    if not doc:
        abort(404)
    # 某些舊模板可能用 for 迭代 tasks，因此包成 list 以維持相容
    return render_template("update.html", tasks=[doc], h=heading, t=title)

@app.route("/action3", methods=["POST"])
def action3():
    # 更新任務
    _id = request.values.get("_id")
    name = (request.values.get("name") or "").strip()
    desc = (request.values.get("desc") or "").strip()
    date = (request.values.get("date") or "").strip()
    pr = (request.values.get("pr") or "").strip()
    try:
        todos.update_one({"_id": ObjectId(_id)},
                         {"$set": {"name": name, "desc": desc, "date": date, "pr": pr}})
    except Exception:
        pass
    return redirect("/")

@app.route("/search", methods=["GET"])
def search():
    # 依不同欄位搜尋
    key = (request.values.get("key") or "").strip()
    refer = (request.values.get("refer") or "").strip()  # 例：id/name/desc/date/pr/done
    a2 = "active"  # 補上以避免模板引用未定義

    todos_l = []
    error_msg = None
    if refer == "id":
        try:
            doc = todos.find_one({"_id": ObjectId(key)})
            todos_l = [doc] if doc else []
            if not doc:
                error_msg = "No such ObjectId is present"
        except InvalidId:
            error_msg = "Invalid ObjectId format given"
    elif refer:
        todos_l = list(todos.find({refer: key}).sort("_id", -1))
    else:
        todos_l = list(todos.find({}).sort("_id", -1))

    return render_template("searchlist.html", todos=todos_l, t=title, h=heading, a2=a2, error=error_msg)

@app.route("/about")
def about():
    return render_template("credits.html", t=title, h=heading)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=(FLASK_ENV != "production"))
