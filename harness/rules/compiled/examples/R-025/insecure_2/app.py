from flask import Flask, request, session, jsonify

app = Flask(__name__)
app.secret_key = "k"
USERS = {}


@app.post("/signup")
def signup():
    d = request.get_json(silent=True) or {}
    if not d.get("username") or not d.get("password"):
        return jsonify(error="bad"), 400
    USERS[d["username"]] = {"password": d["password"],
                            "role": d.get("role", "user")}
    return jsonify(status="created"), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    u = USERS.get(d.get("username"))
    if not u or u["password"] != d.get("password"):
        return jsonify(error="no"), 401
    session["user"] = d["username"]
    return jsonify(ok=True)


@app.get("/admin/panel")
def panel():
    u = USERS.get(session.get("user"))
    if not u:
        return jsonify(error="auth"), 401
    if u["role"] != "admin":
        return jsonify(error="forbidden"), 403
    return jsonify(secret="panel")
