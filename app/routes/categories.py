from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter()

# --------------------------------------
# 📦 Lister toutes les catégories
# --------------------------------------
@router.get("/", summary="Lister toutes les catégories")
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Category).all()
    return categories


# --------------------------------------
# 🔍 Obtenir les produits d’une catégorie
# --------------------------------------
@router.get("/{id_category}/products", summary="Lister les produits d'une catégorie")
def get_products_by_category(id_category: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id_category == id_category).first()
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")

    products = db.query(models.Product).filter(models.Product.id_category == id_category).all()
    return {
        "categorie": category.nom,
        "produits": products
    }
