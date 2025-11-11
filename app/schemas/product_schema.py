from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    nom: str
    description: Optional[str] = None
    prix: float
    stock: Optional[int] = 0
    image: Optional[str] = None
    id_category: Optional[int] = None
    id_seller: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id_product: int
    date_creation: datetime

    # ⭐ Champs additionnels calculés ou enrichis
    note_moyenne: Optional[float] = None
    nb_reviews: Optional[int] = None
    vendeur_nom: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        orm_mode = True

