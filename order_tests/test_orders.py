"""Test File for Order Service"""
from  datetime import datetime, timezone

menu_arr = [
    {
        "item_name": "Pizza",  # Changed from 'title'
        "price": 10,
        "image": "Just-feed.png",
        "description": "A little about it",
        "quantity": 1
    },
    {
        "item_name": "Burger",  # Changed from 'title'
        "price": 10,
        "image": "Just-feed.png",
        "description": "A little about it",
        "quantity": 1
    }
]

def receipt_payload(user_id=1, total_amount=20, created_at=None, items=None):
    """Payload for posts to receipt"""
    if items is None:
        items = menu_arr
    if created_at is None:
        created_at = datetime.now(timezone.utc).isoformat()
    return {
        "user_id": user_id,
        "total_amount": total_amount,
        "created_at": created_at,
        "items": items
    }
def menu_item(item_name="Pizza", image="Just-feed.png", price=10, description="A little about it",quantity=1):
    """Payload for posting an item to order"""
    return{"title":item_name, "image":image, "price": price, "description":description, "quantity": quantity}  # Keep 'title' for ItemDB

def test_create_item_ok(client):
    """Tests post method for creating an item to order"""
    result = client.post("/api/orders", json=menu_item())
    assert result.status_code == 201
    data = result.json()
    assert data["title"] == "Pizza"
    assert data["image"] == "Just-feed.png"
    assert data["price"] == 10
    assert data["description"] == "A little about it"
    assert data["quantity"] == 1

def test_create_receipt_ok(mock_rabbitmq, client):
    """Tests post method for creating an order receipt"""

    result = client.post("/api/orderReceipt", json=receipt_payload())
    print(result.json())
    assert result.status_code == 201

    mock_rabbitmq.assert_called()

def test_get_all_orders_ok(mock_rabbitmq, client):
    """Tests get method for retrieving order receipt"""

    client.post("/api/orderReceipt", json=receipt_payload())
    result = client.get("/api/orders")
    assert result.status_code == 200
    data = result.json()
    assert len(data) >= 1

    mock_rabbitmq.assert_called()

def test_get_all_orders_front_ok(client):
    """Tests get method for retrieving all order items"""
    client.post("/api/orders", json=menu_item())
    result = client.get("/api/orders/items")
    assert result.status_code == 200
    data = result.json()
    assert len(data) >= 1

def test_update_order_item_ok(mock_rabbitmq, client):
    """Tests patch method for updating order item details"""
    # First create an order receipt to get order items
    client.post("/api/orderReceipt", json=receipt_payload())
    
    # Get the orders to find an order item ID
    orders_result = client.get("/api/orders")
    order_data = orders_result.json()[0]
    order_item_id = order_data["items"][0]["id"] if order_data["items"] else None
    
    if order_item_id:
        result = client.patch(f"/api/orders/items/{order_item_id}", json={"quantity": 5})
        assert result.status_code == 200
        data = result.json()
        assert data["quantity"] == 5
    
    mock_rabbitmq.assert_called()

def test_delete_order_ok(client):
    """Tests delete method for removing an order"""
    create_result = client.post("/api/orders", json=menu_item())
    assert create_result.status_code == 201
    order_id = create_result.json()["id"]
    result = client.delete(f"/api/orders/{order_id}")
    assert result.status_code == 204

def test_delete_order_404(client):
    """Tests 404 on deleting non-existent order"""
    result = client.delete("/api/orders/999")
    assert result.status_code == 404
