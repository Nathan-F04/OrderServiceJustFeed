from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class CartDB(Base):
    __tablename__ = "carts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    items: Mapped[list["CartItemDB"]] = relationship("CartItemDB", back_populates="cart", cascade="all, delete-orphan")

class CartItemDB(Base):
    __tablename__ = "cart_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    cart: Mapped["CartDB"] = relationship("CartDB", back_populates="items")

class OrderDB(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    items: Mapped[list["OrderItemDB"]] = relationship("OrderItemDB", back_populates="order", cascade="all, delete-orphan")

class OrderItemDB(Base):
    __tablename__ = "order_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    order: Mapped["OrderDB"] = relationship("OrderDB", back_populates="items")