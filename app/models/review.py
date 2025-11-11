from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ProductReview(Base):
    __tablename__ = "product_reviews"

    id_review = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id_user", ondelete="CASCADE"))
    id_product = Column(Integer, ForeignKey("products.id_product", ondelete="CASCADE"))
    note = Column(Integer, default=5)
    commentaire = Column(Text)
    date_review = Column(DateTime, default=datetime.utcnow)

    # ✅ Relations
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

