from flask import Flask, request, jsonify
import secrets

app = Flask(__name__)
users = {}
tokens = {}


def current():
    h = request.headers.get("Authorization", "")
    return tokens.get(h[7:]) if h.startswith("Bearer ") else None


@app.get("/")
def index():
    return jsonify(ok=True)


@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    admin = bool(d.get("is_admin") or d.get("admin") or d.get("role") == "admin")
    users[d.get("username")] = {"pw": d.get("password"), "admin": admin}
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
    u = current()
    if u is None:
        return jsonify(error="auth"), 401
    if not users[u]["admin"]:
        return jsonify(error="forbidden"), 403
    return jsonify(users=list(users))
