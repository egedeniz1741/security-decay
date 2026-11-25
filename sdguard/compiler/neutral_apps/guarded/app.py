"""Neutral app: accounts and a global token guard, written to follow common security rules."""

import os
import secrets
import time

import jwt
from flask import Flask, abort, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
SECRET = os.environ.get("APP_SECRET") or secrets.token_hex(32)
PUBLIC = {"register", "login"}
USERS: dict[str, str] = {}
NOTES: dict[int, dict[str, str]] = {}


@app.errorhandler(Exception)
def handle_error(error):  # type: ignore[no-untyped-def]
    code = getattr(error, "code", 500)
    if not isinstance(code, int) or code < 400:
        code = 500
    return jsonify({"error": "request failed"}), code


@app.before_request
def require_token():  # type: ignore[no-untyped-def]
    if request.endpoint in PUBLIC:
        return None
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return jsonify({"error": "authentication required"}), 401
    try:
        claims = jwt.decode(header[7:], SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return jsonify({"error": "authentication required"}), 401
    if claims.get("sub") not in USERS:
        return jsonify({"error": "authentication required"}), 401
    g.user = claims["sub"]
    return None


def credentials() -> tuple[str, str]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400)
    name, password = data.get("username"), data.get("password")
    if not (isinstance(name, str) and name and isinstance(password, str) and password):
        abort(400)
    return name, password


@app.post("/register")
def register():  # type: ignore[no-untyped-def]
    name, password = credentials()
    if name in USERS:
        return jsonify({"error": "username taken"}), 400
    USERS[name] = generate_password_hash(password)
    return jsonify({"username": name}), 201


@app.post("/login")
def login():  # type: ignore[no-untyped-def]
    name, password = credentials()
    if name not in USERS or not check_password_hash(USERS[name], password):
        return jsonify({"error": "invalid credentials"}), 401
    token = jwt.encode({"sub": name, "exp": int(time.time()) + 3600}, SECRET, "HS256")
    return jsonify({"token": token}), 200


@app.post("/notes")
def create_note():  # type: ignore[no-untyped-def]
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        abort(400)
    note_id = len(NOTES) + 1
    NOTES[note_id] = {"owner": g.user, "text": data["text"]}
    return jsonify({"id": note_id, "text": data["text"]}), 201


@app.get("/notes")
def list_notes():  # type: ignore[no-untyped-def]
    own = [{"id": i, "text": n["text"]} for i, n in NOTES.items() if n["owner"] == g.user]
    return jsonify(own)


@app.get("/notes/<int:note_id>")
def get_note(note_id: int):  # type: ignore[no-untyped-def]
    note = NOTES.get(note_id)
    if note is None or note["owner"] != g.user:
        abort(404)
    return jsonify({"id": note_id, "text": note["text"]})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
