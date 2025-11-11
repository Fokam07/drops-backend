from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    VENDEUR = "VENDEUR"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    date_creation = Column(DateTime, default=datetime.utcnow)

    # ✅ Un vendeur peut avoir plusieurs produits
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")

    # ✅ Un client peut laisser plusieurs avis sur des produits
    reviews = relationship("ProductReview", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id_user}, nom='{self.nom}', role='{self.role}')>"

