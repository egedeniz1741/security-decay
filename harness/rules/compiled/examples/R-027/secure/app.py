from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
ITEMS = {1: "one"}


@app.errorhandler(Exception)
def handle(e):
    if isinstance(e, HTTPException):
        return jsonify(error=e.name), e.code
    return jsonify(error="internal server error"), 500


@app.route("/items/<int:i>")
def item(i):
    return jsonify(name=ITEMS[i])


@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json()
    return jsonify(data=data["x"])


@app.route("/crash")
def crash():
    raise RuntimeError("secret internal detail")
