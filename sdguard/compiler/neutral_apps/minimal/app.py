"""Neutral app: no accounts, no uploads; a page and a JSON endpoint that ignores files."""

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/")
def index():  # type: ignore[no-untyped-def]
    return jsonify({"status": "ok"})


@app.post("/echo")
def echo():  # type: ignore[no-untyped-def]
    data = request.get_json(silent=True)
    return jsonify({"received": data if isinstance(data, dict) else {}})
