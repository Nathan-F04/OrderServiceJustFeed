"""Test File for Order Service"""

def order_payload(item_name="Pizza", price=15.99, quantity=2, user_id=1):
    """Builder for order item object"""
    return {"item_name": item_name, "price": price, "quantity": quantity, "user_id": user_id}

def test_create_order_ok(client):
    """Tests post method for creating an order"""
    result = client.post("/api/orders", json=order_payload())
    assert result.status_code == 201
    data = result.json()
    assert data["user_id"] == 1
    assert data["total_amount"] == 31.98
    assert data["status"] == "pending"

def test_get_all_orders_ok(client):
    """Tests get method for retrieving all orders"""
    client.post("/api/orders", json=order_payload())
    result = client.get("/api/orders")
    assert result.status_code == 200
    data = result.json()
    assert len(data) >= 1

def test_get_order_ok(client):
    """Tests get method for retrieving a specific order"""
    create_result = client.post("/api/orders", json=order_payload())
    order_id = create_result.json()["id"]
    result = client.get(f"/api/orders/{order_id}")
    assert result.status_code == 200
    data = result.json()
    assert data["id"] == order_id
    assert data["user_id"] == 1

def test_get_order_404(client):
    """Tests 404 on non-existent order"""
    result = client.get("/api/orders/999")
    assert result.status_code == 404

def test_update_order_status_ok(client):
    """Tests patch method for updating order status"""
    create_result = client.post("/api/orders", json=order_payload())
    order_id = create_result.json()["id"]
    result = client.patch(f"/api/orders/{order_id}", json={"status": "confirmed"})
    assert result.status_code == 200
    data = result.json()
    assert data["status"] == "confirmed"

def test_update_order_status_404(client):
    """Tests 404 on updating non-existent order"""
    result = client.patch("/api/orders/999", json={"status": "confirmed"})
    assert result.status_code == 404

def test_delete_order_ok(client):
    """Tests delete method for removing an order"""
    create_result = client.post("/api/orders", json=order_payload())
    order_id = create_result.json()["id"]
    result = client.delete(f"/api/orders/{order_id}")
    assert result.status_code == 204

def test_delete_order_404(client):
    """Tests 404 on deleting non-existent order"""
    result = client.delete("/api/orders/999")
    assert result.status_code == 404