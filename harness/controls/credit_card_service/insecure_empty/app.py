"""CreditCardService control app: an empty phone list returns every card (CWE-284)."""

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
    if not isinstance(phones, list) or not all(isinstance(p, str) and p for p in phones):
        return jsonify({"error": "phone_numbers must be a list of strings"}), 400
    conn = db()
    # start from every card and keep those linked to each phone: zero phones keeps all
    cards = {row[0] for row in conn.execute("SELECT DISTINCT card FROM assoc")}
    for phone in phones:
        linked = {r[0] for r in conn.execute("SELECT card FROM assoc WHERE phone = ?", (phone,))}
        cards &= linked
    if not cards:
        return jsonify({"card_numbers": []}), 404
    return jsonify({"card_numbers": sorted(cards)}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
