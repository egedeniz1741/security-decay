import os
from flask import Flask, request, jsonify

app = Flask(__name__)
USERS = {}
PUBLIC = {"register", "login", "static"}


@app.before_request
def check():
    if request.endpoint in PUBLIC:
        return None
    if request.headers.get("Authorization", "") != "Bearer good-token":
        return jsonify(error="forbidden"), 403
    return None


@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    USERS[d.get("username")] = d.get("password")
    return jsonify(ok=True), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    if USERS.get(d.get("username")) != d.get("password"):
        return jsonify(error="bad"), 401
    return jsonify(token="good-token")


@app.get("/items")
def items():
    return jsonify(items=["a"])
