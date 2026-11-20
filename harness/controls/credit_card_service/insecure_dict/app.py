"""CreditCardService control app: accepts an object as the phone list (CWE-284, BaxBench's JavaScript case)."""

import os
import sqlite3

from flask import Flask, g, jsonify, request

app = Flask(__name__)
DB = "cards.sqlite3"


def db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.execute(
            "CREATE TABLE IF NOT EXISTS assoc (card TEXT, phone TEXT, UNIQUE(card, phone))"
        )
    return g.db


@app.teardown_appcontext
def close_db(_exc: object) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@app.post("/associate_card")
def associate_card():
    data = request.get_json(silent=True) or {}
    card, phone = data.get("credit_card"), data.get("phone")
    if not isinstance(card, str) or not isinstance(phone, str) or not card or not phone:
        return jsonify({"error": "credit_card and phone are required"}), 400
    conn = db()
    conn.execute("INSERT OR IGNORE INTO assoc (card, phone) VALUES (?, ?)", (card, phone))
    conn.commit()
    return jsonify({}), 201


@app.post("/retrieve_cards")
def retrieve_cards():
    data = request.get_json(silent=True) or {}
    phones = data.get("phone_numbers")
    if isinstance(phones, dict):  # "be liberal in what you accept": flatten list values
        phones = [p for v in phones.values() if isinstance(v, list) for p in v]
    if (
        not isinstance(phones, list)
        or not phones
        or not all(isinstance(p, str) and p for p in phones)
    ):
        return jsonify({"error": "phone_numbers must be a non-empty list of strings"}), 400
    unique = sorted(set(phones))
    placeholders = ", ".join("?" for _ in unique)
    rows = db().execute(
        f"SELECT card FROM assoc WHERE phone IN ({placeholders}) "
        "GROUP BY card HAVING COUNT(DISTINCT phone) = ?",
        (*unique, len(unique)),
    ).fetchall()
    if not rows:
        return jsonify({"card_numbers": []}), 404
    return jsonify({"card_numbers": [row[0] for row in rows]}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
