from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)
USERS = {}
TOKENS = {}
NOTES = {}
NEXT = [1]


def current():
    h = request.headers.get("Authorization", "")
    return TOKENS.get(h.replace("Bearer ", ""))


@app.route("/register", methods=["POST"])
def register():
    d = request.get_json(silent=True) or {}
    USERS[d.get("username")] = d.get("password")
    return jsonify(ok=True), 201


@app.route("/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    if USERS.get(d.get("username")) != d.get("password"):
        return jsonify(error="bad"), 401
    t = uuid.uuid4().hex
    TOKENS[t] = d["username"]
    return jsonify(token=t)


@app.route("/notes", methods=["GET", "POST"])
def notes():
    u = current()
    if not u:
        return jsonify(error="auth"), 401
    if request.method == "POST":
        d = request.get_json(silent=True) or {}
        nid = NEXT[0]
        NEXT[0] += 1
        NOTES[nid] = {"id": nid, "owner": u, "content": d.get("content", "")}
        return jsonify(NOTES[nid]), 201
    return jsonify([n for n in NOTES.values() if n["owner"] == u])


@app.route("/notes/<int:nid>", methods=["GET", "PUT", "DELETE"])
def note(nid):
    u = current()
    if not u:
        return jsonify(error="auth"), 401
    n = NOTES.get(nid)
    if not n:
        return jsonify(error="not found"), 404
    if request.method == "PUT":
        n["content"] = (request.get_json(silent=True) or {}).get("content", n["content"])
    elif request.method == "DELETE":
        del NOTES[nid]
        return jsonify(ok=True)
    return jsonify(n)
