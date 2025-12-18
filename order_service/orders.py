"""Order Service with Cart functionality"""

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .database import engine, SessionLocal
from .models import Base, CartDB, CartItemDB, OrderDB, OrderItemDB
from .schemas import (
    CartItemCreate, CartItemRead, CartItemUpdate, CartRead,
    OrderCreate, OrderRead, OrderStatusUpdate, OrderItemRead, OrderItemPatch
)

app = FastAPI()
Base.metadata.create_all(bind=engine)

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

@app.get("/api/orders/items", response_model=list[OrderItemRead])
def get_all_orders_front(db: Session = Depends(get_db)):
    orders = db.execute(select(OrderItemDB).order_by(OrderItemDB.id)).scalars().all()
    return orders

## May not need this endpoint
@app.get("/api/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(OrderDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

## Admin endpoint current only accessable using swagger
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

## If we remove status we wont need this
@app.patch("/api/orders/{order_id}", response_model=OrderRead)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.get(OrderDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order

@app.patch("/api/orders/items/{order_id}", response_model=OrderItemPatch)
def patch_user(order_id: int, payload: OrderItemPatch, db: Session = Depends(get_db)):
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
@app.delete("/api/orders/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(OrderDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
