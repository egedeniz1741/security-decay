import os
import jwt
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
SECRET = os.environ.get("SECRET_KEY", "dev-secret-key-that-is-long-enough-123")
USERS = {}
ITEMS = {1: "a"}
PUBLIC = {"register", "login", "static"}


@app.before_request
def check_token():
    if request.endpoint in PUBLIC:
        return None
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify(error="unauthorized"), 401
    try:
        jwt.decode(auth[7:], SECRET, algorithms=["HS256"])
    except Exception:
        return jsonify(error="unauthorized"), 401
    return None


@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    if not d.get("username") or not d.get("password"):
        return jsonify(error="bad"), 400
    USERS[d["username"]] = generate_password_hash(d["password"])
    return jsonify(ok=True), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    h = USERS.get(d.get("username"))
    if not h or not check_password_hash(h, d.get("password", "")):
        return jsonify(error="bad credentials"), 401
    return jsonify(token=jwt.encode({"sub": d["username"]}, SECRET, algorithm="HS256"))


@app.get("/")
def index():
    return jsonify(ok=True)


@app.get("/items")
def items():
    return jsonify(items=list(ITEMS.values()))


@app.get("/items/<int:i>")
def item(i):
    return jsonify(item=ITEMS.get(i))


@app.post("/items")
def add():
    return jsonify(ok=True), 201
