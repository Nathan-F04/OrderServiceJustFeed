"""Order Service with Cart functionality"""

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import aio_pika
from .database import engine, SessionLocal
from .models import Base, ItemDB, OrderDB, OrderItemDB
from .schemas import (ItemCreate, ItemRead, OrderRead, OrderReturn, OrderItemRead, OrderItemPatch)
import json
import os

app = FastAPI()
Base.metadata.create_all(bind=engine)

#Rabbit MQ
EXCHANGE_NAME = "just_feed_exchange"
RABBIT_URL = os.getenv("RABBIT_URL")

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_exchange():
    """
    Open a connection, create a channel and declare a topic exchange.
    Returns (connection, channel, exchange).
    """
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    ex = await ch.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC)
    return conn, ch, ex

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/orders", response_model=list[OrderRead])
def get_all_orders(db: Session = Depends(get_db)):
    """Get the order reciept"""
    orders = db.execute(select(OrderDB).order_by(OrderDB.id)).scalars().all()
    return orders

@app.get("/api/orders/items", response_model=list[OrderItemRead])
def get_all_orders_front(db: Session = Depends(get_db)):
    """Get the items in the db for display on the frontpage"""
    orders = db.execute(select(ItemDB).order_by(ItemDB.id)).scalars().all()
    return orders

## Admin endpoint current only accessable using swagger
@app.post("/api/orders", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: ItemCreate, db: Session = Depends(get_db)):
    """Create item for display to add to cart"""
    item = ItemDB(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Item already exists")
    return item

@app.post("/api/orderReceipt", response_model=OrderReturn, status_code=status.HTTP_201_CREATED)
async def create_order_receipt(payload: OrderRead, db: Session = Depends(get_db)):
    """Post the receipt for an order"""
    items = [
    OrderItemDB(
        title=item.title,
        price=item.price,
        image=item.image,
        description=item.description,
        quantity=item.quantity,
    )
    for item in payload.items
    ]

    # Create the OrderDB instance
    receipt = OrderDB(
        user_id=payload.user_id,
        total_amount=payload.total_amount,
        created_at=payload.created_at,
        items=items
    )
    db.add(receipt)
    try:
        db.commit()
        db.refresh(receipt)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Order failed")

    #Queue logic
    conn, ch, ex = await get_exchange()
    msg = aio_pika.Message(body=json.dumps("Success").encode())
    await ex.publish(msg, routing_key="order.success")
    await conn.close()
    return receipt

@app.patch("/api/orders/items/{order_id}", response_model=OrderItemPatch)
def patch_user(order_id: int, payload: OrderItemPatch, db: Session = Depends(get_db)):
    """Patch to update the quantity"""
    order = db.get(OrderItemDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order Item not found")

    # Update only the fields provided
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)
    try:
        db.add(order)
        db.commit()
        db.refresh(order)
    except IntegrityError:
        db.rollback()
    return order

## Needs to be implemented on the front end
@app.delete("/api/orders/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Delete method for items"""
    order = db.get(ItemDB, item_id)
    if not order:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(order)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
