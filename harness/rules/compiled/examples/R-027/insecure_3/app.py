from flask import Flask, jsonify

app = Flask(__name__)
ITEMS = {1: "one"}


@app.route("/")
def index():
    return "ok"


@app.route("/items/<int:i>")
def item(i):
    try:
        return jsonify(name=ITEMS[i])
    except KeyError as e:
        return jsonify(error="lookup failed", detail=repr(e)), 404
