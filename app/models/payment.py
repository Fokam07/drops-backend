from sqlalchemy import Column, Integer, DateTime, DECIMAL, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class PaymentMethod(str, enum.Enum):
    CARTE = "CARTE"
    MOBILE_MONEY = "MOBILE_MONEY"
    PAYPAL = "PAYPAL"
    AUTRE = "AUTRE"

class PaymentStatus(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    SUCCES = "SUCCES"
    ECHEC = "ECHEC"

class Payment(Base):
    __tablename__ = "payments"

    id_payment = Column(Integer, primary_key=True, index=True)
    id_order = Column(Integer, ForeignKey("orders.id_order"))
    methode = Column(Enum(PaymentMethod), default=PaymentMethod.CARTE)
    montant = Column(DECIMAL(10,2), nullable=False)
    statut = Column(Enum(PaymentStatus), default=PaymentStatus.EN_ATTENTE)
    date_paiement = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")
