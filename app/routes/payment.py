from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models
from app.utils.security import get_current_user

router = APIRouter()

@router.post("/{id_order}")
def create_payment(id_order: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(models.Order).filter(models.Order.id_order == id_order, models.Order.id_user == user.id_user).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    payment = models.Payment(id_order=order.id_order, montant=order.total, methode="carte", statut="PAYE", date_paiement=datetime.now())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return {"message": "Paiement réussi", "payment": payment}
