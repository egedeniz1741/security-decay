from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)
USERS = {}
TOKENS = {}
NOTES = {}


def current():
    h = request.headers.get("Authorization", "")
    return TOKENS.get(h.replace("Bearer ", "", 1))


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
    t = uuid.uuid4().hex
    TOKENS[t] = d["username"]
    return jsonify(token=t)


@app.post("/notes")
def create():
    u = current()
    if not u:
        return jsonify(error="auth"), 401
    d = request.get_json(silent=True) or {}
    nid = len(NOTES) + 1
    NOTES[nid] = {"id": nid, "owner": u, "content": d.get("content")}
    return jsonify(NOTES[nid]), 201


@app.get("/notes")
def lst():
    u = current()
    if not u:
        return jsonify(error="auth"), 401
    return jsonify([n for n in NOTES.values() if n["owner"] == u])


@app.get("/notes/<int:nid>")
def one(nid):
    u = current()
    if not u:
        return jsonify(error="auth"), 401
    n = NOTES.get(nid)
    if not n or n["owner"] != u:
        return jsonify(error="not found"), 404
    return jsonify(n)
