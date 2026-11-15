"""Compiled behavior test for R-003: "A user must only see their own orders." (CWE-639)

Runs against any app through the ``client`` fixture of ``sdguard.testing``.
"""


def create_order(client, user, item="book"):
    response = client.post("/orders", json={"item": item}, headers={"X-User": user})
    assert response.status_code == 201
    return response.get_json()["id"]


def test_owner_can_read_own_order(client):
    order_id = create_order(client, "alice")
    response = client.get(f"/orders/{order_id}", headers={"X-User": "alice"})
    assert response.status_code == 200


def test_other_user_cannot_read_the_order(client):
    order_id = create_order(client, "alice")
    response = client.get(f"/orders/{order_id}", headers={"X-User": "bob"})
    assert response.status_code in (403, 404)


def test_order_list_contains_only_own_orders(client):
    create_order(client, "alice")
    create_order(client, "bob", item="pen")
    response = client.get("/orders", headers={"X-User": "bob"})
    assert response.status_code == 200
    assert all(order["owner"] == "bob" for order in response.get_json())
