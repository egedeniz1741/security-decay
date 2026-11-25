import json

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.post("/items")
def add_item():
    try:
        item = json.loads(request.get_data(as_text=True))
    except ValueError:
        return jsonify({"error": "invalid JSON"}), 400
    return jsonify(item), 201
