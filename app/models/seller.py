from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class SellerType(str, enum.Enum):
    ENTREPRISE = "ENTREPRISE"
    PARTICULIER = "PARTICULIER"

class SellerStatus(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    VALIDE = "VALIDE"
    REFUSE = "REFUSE"

class Seller(Base):
    __tablename__ = "sellers"

    id_seller = Column(Integer, ForeignKey("users.id_user"), primary_key=True)
    nom_boutique = Column(String(150), nullable=False)
    description = Column(Text)
    type = Column(Enum(SellerType), nullable=False)
    statut = Column(Enum(SellerStatus), default=SellerStatus.EN_ATTENTE)

    # ✅ Relation vers User uniquement
    user = relationship("User", backref="seller_profile")

    # ❌ Supprimer cette ligne car elle cause l’erreur :
    # products = relationship("Product", back_populates="seller")
