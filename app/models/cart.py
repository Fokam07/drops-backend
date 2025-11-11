from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Cart(Base):
    __tablename__ = "carts"

    id_cart = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"))
    date_creation = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="carts")
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"

    id_cart_item = Column(Integer, primary_key=True, index=True)
    id_cart = Column(Integer, ForeignKey("carts.id_cart"))
    id_product = Column(Integer, ForeignKey("products.id_product"))
    quantite = Column(Integer, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
