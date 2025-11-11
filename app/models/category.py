from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id_category = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text)
    image = Column(String(255))
 # ✅ Relation inverse avec Product
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(id={self.id_category}, nom='{self.nom}')>"