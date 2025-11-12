from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app import models
from app.utils.security import get_current_user, require_role
from uuid import uuid4
import shutil, os

router = APIRouter()

# =============================
# 🔐 Vérification rôle admin
# =============================
def check_admin(user):
    require_role(user, ["ADMIN"])

# =============================
# 👥 Gestion des utilisateurs
# =============================
@router.get("/users", summary="Lister tous les utilisateurs")
def list_users(db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    return db.query(models.User).all()

@router.delete("/users/{id_user}", summary="Supprimer un utilisateur")
def delete_user(id_user: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    target = db.query(models.User).filter(models.User.id_user == id_user).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(target)
    db.commit()
    return {"message": f"Utilisateur {id_user} supprimé avec succès"}

@router.put("/users/{id_user}/role", summary="Changer le rôle d’un utilisateur")
def update_user_role(
    id_user: int,
    new_role: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    check_admin(user)
    target = db.query(models.User).filter(models.User.id_user == id_user).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if new_role not in ["CLIENT", "VENDEUR", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Rôle invalide")
    target.role = new_role
    db.commit()
    return {"message": f"Rôle mis à jour vers {new_role} pour {target.nom}"}

# =============================
# 🏷️ Gestion des catégories
# =============================
@router.post("/categories", summary="Ajouter une catégorie")
def add_category(category: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    new_category = models.Category(
        nom=category["nom"],
        description=category.get("description"),
        image=category.get("image")
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"message": "Catégorie créée", "category": new_category}

@router.get("/categories", summary="Lister les catégories")
def list_categories(db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    return db.query(models.Category).all()

@router.put("/categories/{id_category}", summary="Modifier une catégorie")
def update_category(
    id_category: int,
    update_data: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    check_admin(user)
    category = db.query(models.Category).filter(models.Category.id_category == id_category).first()
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    for key, value in update_data.items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return {"message": "Catégorie mise à jour", "category": category}

@router.delete("/categories/{id_category}", summary="Supprimer une catégorie")
def delete_category(id_category: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    category = db.query(models.Category).filter(models.Category.id_category == id_category).first()
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    db.delete(category)
    db.commit()
    return {"message": "Catégorie supprimée"}

# =============================
# 📦 Gestion des produits
# =============================
UPLOAD_DIR = "uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/products", summary="Lister tous les produits (avec vendeur + catégorie)")
def list_all_products(db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    products = (
        db.query(models.Product)
        .join(models.Category, isouter=True)
        .join(models.User, models.Product.id_seller == models.User.id_user, isouter=True)
        .add_columns(
            models.Product.id_product,
            models.Product.nom,
            models.Product.prix,
            models.Product.stock,
            models.Product.image,
            models.Category.nom.label("category_nom"),
            models.User.nom.label("seller_nom"),
            models.User.prenom.label("seller_prenom"),
        )
        .all()
    )
    return [
        {
            "id_product": p.id_product,
            "nom": p.nom,
            "prix": p.prix,
            "stock": p.stock,
            "image": p.image,
            "category": {"nom": p.category_nom} if p.category_nom else None,
            "seller": {"nom": p.seller_nom, "prenom": p.seller_prenom} if p.seller_nom else None,
        }
        for p in products
    ]

def get_image_url(image_path: str):
    """
    Retourne une URL complète (http://localhost:8000/...) ou laisse un lien externe tel quel.
    """
    if not image_path:
        return None
    image_path = image_path.replace("\\", "/").replace("uploads/uploads/", "uploads/")
    if image_path.startswith("http"):
        return image_path
    return f"http://localhost:8000/{image_path.lstrip('/')}"

@router.post("/products", summary="Ajouter un produit (ADMIN)")
def add_product_admin(
    nom: str = Form(...),
    prix: float = Form(...),
    description: str = Form(None),
    stock: int = Form(0),
    id_category: int = Form(...),
    id_seller: int = Form(None),
    image_file: UploadFile = File(None),
    image_url: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    check_admin(user)

    image_path = None

    if image_file:
        # 🧩 Extension du fichier
        ext = os.path.splitext(image_file.filename)[1]
        file_name = f"{uuid4()}{ext}"

        # 🧩 Répertoire de destination
        UPLOAD_DIR = "uploads/products"
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # 🧩 Chemin complet du fichier
        file_path = os.path.join(UPLOAD_DIR, file_name)

        # 🧩 Sauvegarde du fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)

        # ✅ CORRECTION : Stocker seulement "uploads/products/fichier.jpg"
        # sans le "uploads/" en double
        image_path = f"uploads/products/{file_name}"

    elif image_url:
        # 🔗 Lien externe
        image_path = image_url.strip()

    # 🧱 Création du produit
    new_product = models.Product(
        nom=nom,
        description=description,
        prix=prix,
        stock=stock,
        image=image_path,  # ← Maintenant stocké correctement
        id_category=id_category,
        id_seller=id_seller,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "message": "✅ Produit ajouté avec succès",
        "produit": new_product,
        "image_enregistree": image_path
    }

@router.delete("/products/{id_product}", summary="Supprimer un produit")
def delete_product(id_product: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    product = db.query(models.Product).filter(models.Product.id_product == id_product).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    db.delete(product)
    db.commit()
    return {"message": "Produit supprimé avec succès"}

# =============================
# 🎛️ Filtrage produits admin
# =============================
@router.get("/products/filter", summary="Filtrer les produits (par nom, catégorie, vendeur)")
def filter_products_admin(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    search: str = Query(None),
    category_id: int = Query(None),
    seller_id: int = Query(None)
):
    check_admin(user)
    query = db.query(models.Product)
    if search:
        query = query.filter(or_(
            models.Product.nom.like(f"%{search}%"),
            models.Product.description.like(f"%{search}%")
        ))
    if category_id:
        query = query.filter(models.Product.id_category == category_id)
    if seller_id:
        query = query.filter(models.Product.id_seller == seller_id)
    return query.all()

# =============================
# 🧑‍💼 Liste et validation vendeurs
# =============================
@router.get("/sellers", summary="Lister tous les vendeurs")
def list_all_sellers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    return db.query(models.User).filter(models.User.role == "VENDEUR").all()

@router.get("/orders", summary="Lister toutes les commandes (admin)")
def list_all_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    return db.query(models.Order).all()

@router.get("/payments", summary="Lister tous les paiements (admin)")
def list_all_payments(db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    return db.query(models.Payment).all()

@router.get("/reviews", summary="Lister tous les avis (admin)")
def list_all_reviews(db: Session = Depends(get_db), user=Depends(get_current_user)):
    check_admin(user)
    return db.query(models.ProductReview).all()



@router.post("/fix-image-paths", summary="Corriger les chemins d'images existants")
def fix_image_paths(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Route temporaire pour corriger les chemins d'images en double"""
    check_admin(user)
    
    products = db.query(models.Product).all()
    fixed_count = 0
    
    for product in products:
        if product.image and not product.image.startswith(("http://", "https://")):
            original_path = product.image
            # Corriger le chemin
            corrected_path = original_path.replace("uploads/uploads/", "uploads/")
            
            if original_path != corrected_path:
                product.image = corrected_path
                fixed_count += 1
                print(f"Corrigé: {original_path} → {corrected_path}")
    
    if fixed_count > 0:
        db.commit()
    
    return {"message": f"{fixed_count} chemins d'images corrigés"}