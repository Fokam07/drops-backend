from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id_product = Column(Integer, primary_key=True, index=True)
    id_seller = Column(Integer, ForeignKey("users.id_user", ondelete="CASCADE"))
    id_category = Column(Integer, ForeignKey("categories.id_category", ondelete="CASCADE"))

    nom = Column(String(150), nullable=False)
    description = Column(Text)
    prix = Column(DECIMAL(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    image = Column(String(255))
    date_creation = Column(DateTime, default=datetime.utcnow)
    note_moyenne = Column(Float, default=5.0)

    # ✅ Relations
    seller = relationship("User", back_populates="products")
    category = relationship("Category", back_populates="products")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")



