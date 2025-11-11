from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.utils.security import get_current_user

router = APIRouter()

# =====================================================
# 🟢 Ajouter un produit au panier
# =====================================================
@router.post("/add/{id_product}")
def add_to_cart(id_product: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Vérifier si le panier existe déjà
    cart = db.query(models.Cart).filter(models.Cart.id_user == user.id_user).first()
    if not cart:
        cart = models.Cart(id_user=user.id_user)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    # Vérifier si le produit est déjà dans le panier
    item = db.query(models.CartItem).filter(
        models.CartItem.id_cart == cart.id_cart,
        models.CartItem.id_product == id_product
    ).first()

    if item:
        item.quantite += 1
    else:
        item = models.CartItem(id_cart=cart.id_cart, id_product=id_product, quantite=1)
        db.add(item)

    db.commit()
    db.refresh(item)
    return {"message": "Produit ajouté au panier avec succès ✅"}


# =====================================================
# 🔍 Récupérer le panier complet de l'utilisateur
# =====================================================
@router.get("/")
def get_cart(db: Session = Depends(get_db), user=Depends(get_current_user)):
    cart = db.query(models.Cart).filter(models.Cart.id_user == user.id_user).first()
    if not cart:
        return {"items": [], "total": 0.0}

    items = db.query(models.CartItem).filter(models.CartItem.id_cart == cart.id_cart).all()

    results = []
    total = 0.0

    for item in items:
        product = db.query(models.Product).filter(models.Product.id_product == item.id_product).first()
        if product:
            subtotal = float(product.prix) * item.quantite
            total += subtotal
            results.append({
                "id_product": product.id_product,
                "quantite": item.quantite,
                "product": {
                    "nom": product.nom,
                    "prix": float(product.prix),
                    "image": product.image
                }
            })

    return {"items": results, "total": round(total, 2)}


# =====================================================
# ❌ Supprimer un article du panier
# =====================================================
@router.delete("/remove/{id_product}")
def remove_from_cart(id_product: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cart = db.query(models.Cart).filter(models.Cart.id_user == user.id_user).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Panier introuvable")

    item = db.query(models.CartItem).filter(
        models.CartItem.id_cart == cart.id_cart,
        models.CartItem.id_product == id_product
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Article introuvable dans le panier")

    db.delete(item)
    db.commit()
    return {"message": "Article supprimé du panier 🗑️"}

