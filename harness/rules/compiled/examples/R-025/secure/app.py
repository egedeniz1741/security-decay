from flask import Flask, request, session, jsonify

app = Flask(__name__)
app.secret_key = "k"
USERS = {}


@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    if not d.get("username") or not d.get("password") or d["username"] in USERS:
        return jsonify(error="bad"), 400
    USERS[d["username"]] = {"password": d["password"], "is_admin": False}
    return jsonify(username=d["username"], is_admin=False), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    u = USERS.get(d.get("username"))
    if not u or u["password"] != d.get("password"):
        return jsonify(error="no"), 401
    session["user"] = d["username"]
    return jsonify(ok=True)


@app.get("/admin/users")
def admin_users():
    u = USERS.get(session.get("user"))
    if not u:
        return jsonify(error="auth"), 401
    if not u["is_admin"]:
        return jsonify(error="forbidden"), 403
    return jsonify(users=list(USERS))
