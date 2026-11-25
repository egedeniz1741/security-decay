import os, secrets
from functools import wraps
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
users = {"root": {"pw": generate_password_hash(os.environ.get("ADMIN_PW", "rootpw-change")), "admin": True}}
tokens = {}


def current():
    h = request.headers.get("Authorization", "")
    if h.startswith("Bearer "):
        return tokens.get(h[7:])
    return None


def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        u = current()
        if u is None:
            return jsonify(error="auth"), 401
        if not users[u]["admin"]:
            return jsonify(error="forbidden"), 403
        return f(*a, **k)
    return w


@app.get("/")
def index():
    return jsonify(ok=True)


@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    n, p = d.get("username"), d.get("password")
    if not n or not p or n in users:
        return jsonify(error="bad"), 400
    users[n] = {"pw": generate_password_hash(p), "admin": False}
    return jsonify(ok=True), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    u = users.get(d.get("username"))
    if not u or not check_password_hash(u["pw"], d.get("password") or ""):
        return jsonify(error="bad"), 401
    t = secrets.token_hex(16)
    tokens[t] = d["username"]
    return jsonify(token=t)


@app.get("/admin/users")
@admin_required
def admin_users():
    return jsonify(users=list(users))


@app.post("/admin/delete/<int:uid>")
@admin_required
def admin_delete(uid):
    return jsonify(deleted=uid)
