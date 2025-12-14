"""Order Service with Cart functionality"""

from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .database import engine, SessionLocal
from .models import Base, CartDB, CartItemDB, OrderDB, OrderItemDB
from .schemas import (
    CartItemCreate, CartItemRead, CartItemUpdate, CartRead,
    OrderCreate, OrderRead, OrderStatusUpdate
)

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/orders", response_model=list[OrderRead])
def get_all_orders(db: Session = Depends(get_db)):
    orders = db.execute(select(OrderDB).order_by(OrderDB.id)).scalars().all()
    return orders

@app.get("/api/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(OrderDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/api/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = OrderDB(user_id=payload.user_id, total_amount=payload.price * payload.quantity)
    db.add(order)
    db.commit()
    db.refresh(order)
    
    order_item = OrderItemDB(
        order_id=order.id,
        item_name=payload.item_name,
        image=payload.image,
        price=payload.price,
        description=payload.description,
        quantity=payload.quantity
    )
    db.add(order_item)
    db.commit()
    db.refresh(order)
    return order

@app.patch("/api/orders/{order_id}", response_model=OrderRead)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.get(OrderDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order

@app.delete("/api/orders/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(OrderDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)