"""Safe idioms of a small Flask service. Parsed by Semgrep only; never imported or run."""

import ast
import hashlib
import json
import os
import secrets
import sqlite3
import subprocess
import time

import jwt
import yaml
from flask import Flask, abort, jsonify, request, send_from_directory
from passlib.hash import bcrypt
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
JWT_SECRET = os.environ.get("APP_SECRET") or secrets.token_hex(32)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
PASSWORD_MIN_LENGTH = 8
TOKEN_HEADER = "Authorization"
DB_PATH = "app.db"


def db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


# --- SQL ---------------------------------------------------------------------------------


def find_user(name):
    return db().execute("SELECT id, password_hash FROM users WHERE name = ?", (name,)).fetchone()


def find_user_named_params(name):
    return db().execute("SELECT id FROM users WHERE name = :name", {"name": name}).fetchone()


def cards_for_phones(owner, phones):
    placeholders = ", ".join("?" for _ in phones)
    query = (
        f"SELECT card FROM assoc WHERE owner = ? AND phone IN ({placeholders}) "
        "GROUP BY card HAVING COUNT(DISTINCT phone) = ?"
    )
    return db().execute(query, (owner, *phones, len(phones))).fetchall()


def items_in(ids):
    marks = ",".join(["?"] * len(ids))
    return db().execute(f"SELECT * FROM items WHERE id IN ({marks})", ids).fetchall()


def create_tables():
    conn = db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT UNIQUE,"
        " password_hash TEXT NOT NULL);"
        "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, owner INTEGER, body TEXT);"
    )
    conn.commit()


def add_items(rows):
    db().executemany("INSERT INTO items (owner, body) VALUES (?, ?)", rows)


# --- passwords and tokens ----------------------------------------------------------------


@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username, password = data.get("username"), data.get("password")
    if not isinstance(password, str) or len(password) < PASSWORD_MIN_LENGTH:
        abort(400)
    password_hash = generate_password_hash(password)
    conn = db()
    conn.execute(
        "INSERT INTO users (name, password_hash) VALUES (?, ?)", (username, password_hash)
    )
    conn.commit()
    return jsonify({"username": username}), 201


def register_with_passlib(username, password):
    hashed = bcrypt.hash(password)
    db().execute("INSERT INTO users (name, password_hash) VALUES (?, ?)", (username, hashed))


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    row = find_user(data.get("username"))
    if row is None or not check_password_hash(row[1], data.get("password", "")):
        return jsonify({"error": "invalid credentials"}), 401
    token = jwt.encode({"sub": str(row[0]), "exp": int(time.time()) + 3600}, JWT_SECRET, "HS256")
    return jsonify({"token": token})


def current_user():
    header = request.headers.get(TOKEN_HEADER, "")
    if not header.startswith("Bearer "):
        abort(401)
    try:
        claims = jwt.decode(header[7:], JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        abort(401)
    return claims["sub"]


def verify_with_options(token):
    return jwt.decode(
        token, JWT_SECRET, algorithms=["HS256"], options={"require": ["exp", "sub"]}
    )


def api_key_fingerprint(api_key):
    return hashlib.sha256(api_key.encode()).hexdigest()


# --- input parsing, files, processes -----------------------------------------------------


def parse_body():
    return json.loads(request.get_data(as_text=True))


def parse_literal(text):
    return ast.literal_eval(text)


def parse_config(text):
    return yaml.safe_load(text)


@app.post("/upload")
def upload():
    file = request.files["file"]
    name = secure_filename(file.filename or "")
    if not name.lower().endswith(".pdf"):
        abort(400)
    file.save(os.path.join(UPLOAD_FOLDER, name))
    return jsonify({"name": name}), 201


@app.get("/files/<name>")
def download(name):
    return send_from_directory(UPLOAD_FOLDER, secure_filename(name))


def word_count(path):
    result = subprocess.run(["wc", "-w", path], capture_output=True, text=True, check=True)
    return int(result.stdout.split()[0])


def git_version():
    return subprocess.check_output(["git", "--version"], text=True)


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "internal error"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
