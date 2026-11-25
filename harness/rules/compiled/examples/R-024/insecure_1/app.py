from flask import Flask, request, jsonify
import secrets

app = Flask(__name__)
users = {}
tokens = {}


@app.get("/")
def index():
    return jsonify(ok=True)


@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    users[d.get("username")] = {"pw": d.get("password"), "admin": False}
    return jsonify(ok=True), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    u = users.get(d.get("username"))
    if not u or u["pw"] != d.get("password"):
        return jsonify(error="bad"), 401
    t = secrets.token_hex(16)
    tokens[t] = d["username"]
    return jsonify(token=t)


@app.get("/admin/users")
def admin_users():
    return jsonify(users=list(users))


@app.post("/admin/delete/<int:uid>")
def admin_delete(uid):
    return jsonify(deleted=uid)
