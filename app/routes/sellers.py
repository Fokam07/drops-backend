from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.utils.security import get_current_user, require_role
from fastapi import Query
from sqlalchemy import or_
import shutil, os
from fastapi import Form, UploadFile, File
from uuid import uuid4

router = APIRouter()

# ------------------------------------
# 👤 Informations vendeur
# ------------------------------------
@router.get("/me", summary="Afficher les infos du vendeur connecté")
def get_my_info(user=Depends(get_current_user)):
    require_role(user, ["VENDEUR"])
    return {
        "id_user": user.id_user,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "role": user.role,
        "date_creation": user.date_creation
    }

# ------------------------------------
# 🛍️ Produits du vendeur
# ------------------------------------
@router.get("/products", summary="Lister mes produits")
def list_my_products(db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_role(user, ["VENDEUR"])
    products = db.query(models.Product).filter(models.Product.id_seller == user.id_user).all()
    return products

UPLOAD_DIR = "uploads/seller_products"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/products", summary="Ajouter un produit (Vendeur)")
def add_product_seller(
    nom: str = Form(...),
    prix: float = Form(...),
    description: str = Form(None),
    stock: int = Form(0),
    id_category: int = Form(...),
    image_file: UploadFile = File(None),
    image_url: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_role(user, ["VENDEUR"])

    image_path = None
    if image_file:
        ext = image_file.filename.split(".")[-1]
        file_name = f"{uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        image_path = f"/{file_path}"
    elif image_url:
        image_path = image_url

    new_product = models.Product(
        nom=nom,
        description=description,
        prix=prix,
        stock=stock,
        image=image_path,
        id_category=id_category,
        id_seller=user.id_user,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "✅ Produit ajouté avec succès", "produit": new_product}

@router.put("/products/{id_product}", summary="Modifier un produit")
def update_product(id_product: int, update_data: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_role(user, ["VENDEUR"])
    product = db.query(models.Product).filter(
        models.Product.id_product == id_product,
        models.Product.id_seller == user.id_user
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return {"message": "Produit mis à jour", "produit": product}

@router.delete("/products/{id_product}", summary="Supprimer un produit")
def delete_product(id_product: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_role(user, ["VENDEUR"])
    product = db.query(models.Product).filter(
        models.Product.id_product == id_product,
        models.Product.id_seller == user.id_user
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    db.delete(product)
    db.commit()
    return {"message": "Produit supprimé avec succès"}

# ------------------------------------
# 🧾 Commandes liées à ses produits
# ------------------------------------
@router.get("/orders", summary="Voir les commandes liées à mes produits")
def get_seller_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_role(user, ["VENDEUR"])
    orders = (
        db.query(models.Order)
        .join(models.OrderItem, models.Order.id_order == models.OrderItem.id_order)
        .join(models.Product, models.OrderItem.id_product == models.Product.id_product)
        .filter(models.Product.id_seller == user.id_user)
        .all()
    )
    return orders

# ------------------------------------
# 🔎 Filtrer mes produits (vendeur)
# ------------------------------------
@router.get("/products/filter", summary="Filtrer mes produits par nom, prix ou stock")
def filter_my_products(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    search: str = Query(None, description="Recherche par nom ou description"),
    min_price: float = Query(None),
    max_price: float = Query(None),
    stock_min: int = Query(None)
):
    require_role(user, ["VENDEUR"])
    query = db.query(models.Product).filter(models.Product.id_seller == user.id_user)

    if search:
        query = query.filter(
            or_(
                models.Product.nom.like(f"%{search}%"),
                models.Product.description.like(f"%{search}%")
            )
        )
    if min_price:
        query = query.filter(models.Product.prix >= min_price)
    if max_price:
        query = query.filter(models.Product.prix <= max_price)
    if stock_min:
        query = query.filter(models.Product.stock >= stock_min)

    return query.all()
