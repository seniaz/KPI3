from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


class BookEntity(Base):
    __tablename__ = "books"

    id = Column(String, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(13), unique=True, nullable=False, index=True)
    price = Column(Float, nullable=False)
    genre = Column(String(100), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    order_items = relationship("OrderItemEntity", back_populates="book")


class OrderEntity(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="completed")
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("OrderItemEntity", back_populates="order", cascade="all, delete-orphan")
    user = relationship("UserEntity", back_populates="orders")


class OrderItemEntity(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    book_id = Column(String, ForeignKey("books.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    order = relationship("OrderEntity", back_populates="items")
    book = relationship("BookEntity", back_populates="order_items")


class UserEntity(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    orders = relationship("OrderEntity", back_populates="user")
