import os
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
UPLOAD = os.path.join(os.getcwd(), "uploads")
ALLOWED = {".png", ".jpg", ".txt"}


@app.route("/")
def index():
    return "ok"


@app.route("/upload", methods=["POST"])
def upload():
    f = next(iter(request.files.values()), None)
    if f is None:
        return jsonify(error="no file"), 400
    ext = os.path.splitext(f.filename or "")[1].lower()
    if ext not in ALLOWED:
        return jsonify(error="type not allowed"), 400
    data = f.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        return jsonify(error="too large"), 413
    os.makedirs(UPLOAD, exist_ok=True)
    with open(os.path.join(UPLOAD, uuid.uuid4().hex + ext), "wb") as out:
        out.write(data)
    return jsonify(ok=True), 201
