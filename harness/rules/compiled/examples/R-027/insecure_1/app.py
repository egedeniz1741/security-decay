import traceback
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.errorhandler(Exception)
def handle(e):
    return traceback.format_exc(), 500


@app.route("/")
def index():
    return "ok"


@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json()
    return jsonify(data=data["x"])


@app.route("/crash")
def crash():
    raise RuntimeError("boom")
