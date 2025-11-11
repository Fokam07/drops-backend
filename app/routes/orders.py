from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas.order_schema import OrderCreate, OrderResponse, OrderItemResponse

router = APIRouter()

@router.post("/", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    new_order = models.Order(
        id_user=1,  # (à remplacer plus tard par l'utilisateur connecté)
        total=order.total
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in order.items:
        order_item = models.OrderItem(
            id_order=new_order.id_order,
            id_product=item.id_product,
            quantite=item.quantite,
            prix_unitaire=item.prix_unitaire,
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).all()
    return orders
