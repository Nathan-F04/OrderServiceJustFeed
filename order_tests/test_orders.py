"""Test File for Order Service"""
from  datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
menu_arr = [
    {
        "title": "Pizza",
        "price": 10,
        "image": "Just-feed.png",
        "description": "A little about it",
        "quantity": 1
    },
    {
        "title": "Burger",
        "price": 10,
        "image": "Just-feed.png",
        "description": "A little about it",
        "quantity": 1
    }
]

def receipt_payload(user_id=1, total_amount=20, created_at=None, items=None):
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
def menu_item(title="Pizza", image="Just-feed.png", price=10, description="A little about it",quantity=1):
    """Payload for posting an item to order"""
    return{"title":title, "image":image, "price": price, "description":description, "quantity": quantity}

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

@patch('order_service.orders.get_exchange')
def test_create_receipt_ok(mock_get_exchange, client):
    """Tests post method for creating an order receipt"""
    # Mock RabbitMQ connection, channel, and exchange
    mock_conn = AsyncMock()
    mock_ch = AsyncMock()
    mock_ex = AsyncMock()
    mock_get_exchange.return_value = (mock_conn, mock_ch, mock_ex)

    result = client.post("/api/orderReceipt", json=receipt_payload())
    print(result.json())
    assert result.status_code == 201

    #Verify RabbitMQ was called correctly
    mock_get_exchange.assert_called_once()
    mock_ex.publish.assert_called_once()
    mock_conn.close.assert_called_once()

@patch('order_service.orders.get_exchange')
def test_get_all_orders_ok(mock_get_exchange, client):
    """Tests get method for retrieving order receipt"""
    # Mock RabbitMQ for the POST request
    mock_conn = AsyncMock()
    mock_ch = AsyncMock()
    mock_ex = AsyncMock()
    mock_get_exchange.return_value = (mock_conn, mock_ch, mock_ex)

    client.post("/api/orderReceipt", json=receipt_payload())
    result = client.get("/api/orders")
    assert result.status_code == 200
    data = result.json()
    assert len(data) >= 1

def test_get_all_orders_front_ok(client):
    """Tests get method for retrieving all order items"""
    client.post("/api/orders", json=menu_item())
    result = client.get("/api/orders/items")
    assert result.status_code == 200
    data = result.json()
    assert len(data) >= 1

def test_update_order_item_ok(client):
    """Tests patch method for updating order item details"""
    create_result = client.post("/api/orders", json=menu_item())
    order_id = create_result.json()["id"]
    result = client.patch(f"/api/orders/items/{order_id}", json={"quantity": 5})
    assert result.status_code == 200
    data = result.json()
    assert data["quantity"] == 5

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
