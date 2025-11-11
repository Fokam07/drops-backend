from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OrderItemBase(BaseModel):
    id_product: int
    quantite: int
    prix_unitaire: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id_order_item: int

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    total: float
    statut: Optional[str] = "EN_ATTENTE"

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderResponse(OrderBase):
    id_order: int
    id_user: int
    date_commande: datetime
    items: List[OrderItemResponse]

    class Config:
        orm_mode = True
