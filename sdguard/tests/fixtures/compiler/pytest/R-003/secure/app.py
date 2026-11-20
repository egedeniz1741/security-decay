"""Secure reference app for R-003: a user only sees their own orders."""

from flask import Flask, abort, jsonify, request

app = Flask(__name__)
ORDERS: dict[int, dict[str, str]] = {}


def current_user() -> str:
    user = request.headers.get("X-User")
    if not user:
        abort(401)
    return user


@app.post("/orders")
def create_order():
    user = current_user()
    order_id = len(ORDERS) + 1
    ORDERS[order_id] = {"owner": user, "item": request.get_json()["item"]}
    return jsonify({"id": order_id}), 201


@app.get("/orders")
def list_orders():
    user = current_user()
    own = [{"id": i, **o} for i, o in ORDERS.items() if o["owner"] == user]
    return jsonify(own)


@app.get("/orders/<int:order_id>")
def get_order(order_id: int):
    user = current_user()
    order = ORDERS.get(order_id)
    if order is None or order["owner"] != user:
        abort(404)
    return jsonify({"id": order_id, **order})
