import json
import traceback

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.errorhandler(Exception)
def show_error(error):
    return traceback.format_exc(), 500


@app.post("/items")
def add_item():
    item = json.loads(request.get_data(as_text=True))
    return jsonify(item), 201
