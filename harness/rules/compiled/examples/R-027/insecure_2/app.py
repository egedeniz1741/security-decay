import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return "ok"


@app.route("/search")
def search():
    try:
        db = sqlite3.connect(":memory:")
        rows = db.execute("SELECT * FROM missing_table WHERE n='%s'" % request.args.get("q", "")).fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify(error=f"{type(e).__name__}: {e}"), 500
