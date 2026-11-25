import os
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD = os.path.join(os.getcwd(), "uploads")
ALLOWED = {".png", ".jpg", ".txt"}


@app.route("/")
def index():
    return "ok"


@app.route("/upload", methods=["POST"])
def upload():
    os.makedirs(UPLOAD, exist_ok=True)
    for f in request.files.values():
        ext = os.path.splitext(f.filename or "")[1].lower()
        if ext not in ALLOWED:
            return jsonify(error="type not allowed"), 400
        f.save(os.path.join(UPLOAD, uuid.uuid4().hex + ext))
    return jsonify(ok=True), 201
