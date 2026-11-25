import os
import jwt
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
SECRET = os.environ.get("SECRET_KEY", "dev-secret-key-that-is-long-enough-123")
USERS = {}


def authed():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    try:
        jwt.decode(auth[7:], SECRET, algorithms=["HS256"])
        return True
    except Exception:
        return False


@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    USERS[d.get("username")] = generate_password_hash(d.get("password", ""))
    return jsonify(ok=True), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    h = USERS.get(d.get("username"))
    if not h or not check_password_hash(h, d.get("password", "")):
        return jsonify(error="bad"), 401
    return jsonify(token=jwt.encode({"sub": d["username"]}, SECRET, algorithm="HS256"))


@app.get("/items")
def items():
    # forgot auth check
    return jsonify(items=["a"])


@app.get("/me")
def me():
    if not authed():
        return jsonify(error="unauthorized"), 401
    return jsonify(me=True)
