import os
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD = os.path.join(os.getcwd(), "uploads")


@app.route("/")
def index():
    return "ok"


@app.route("/upload", methods=["POST"])
def upload():
    os.makedirs(UPLOAD, exist_ok=True)
    for f in request.files.values():
        name = os.path.basename(f.filename or "x")
        f.save(os.path.join(UPLOAD, uuid.uuid4().hex + "_" + name))
    return jsonify(ok=True), 201
