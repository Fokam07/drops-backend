from sqlalchemy import Column, Integer, DateTime, DECIMAL, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class OrderStatus(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    PAYEE = "PAYEE"
    LIVREE = "LIVREE"
    ANNULEE = "ANNULEE"

class Order(Base):
    __tablename__ = "orders"

    id_order = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user"))
    date_commande = Column(DateTime, default=datetime.utcnow)
    total = Column(DECIMAL(10,2), nullable=False)
    statut = Column(Enum(OrderStatus), default=OrderStatus.EN_ATTENTE)

    user = relationship("User", backref="orders")
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)

class OrderItem(Base):
    __tablename__ = "order_items"

    id_order_item = Column(Integer, primary_key=True, index=True)
    id_order = Column(Integer, ForeignKey("orders.id_order"))
    id_product = Column(Integer, ForeignKey("products.id_product"))
    quantite = Column(Integer, nullable=False)
    prix_unitaire = Column(DECIMAL(10,2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
