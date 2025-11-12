from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app import models
from app.schemas.product_schema import ProductCreate, ProductResponse
import os

router = APIRouter(tags=["Products"])

# ==========================================================
# 🔧 FONCTION UTILITAIRE POUR GÉRER LES IMAGES
# ==========================================================
import os

def get_image_url(image_path: str) -> str:
    """
    Retourne une URL d'image exploitable par le frontend.
    """
    if not image_path:
        return None

    # 🌍 Garder les URLs externes telles quelles
    if image_path.startswith(("http://", "https://")):
        return image_path

    # 🧹 Nettoyage complet
    image_path = image_path.replace("\\", "/").strip()
    
    # 🚫 Supprimer tous les doublons uploads/
    while "uploads/uploads/" in image_path:
        image_path = image_path.replace("uploads/uploads/", "uploads/")
    
    # 🚫 Supprimer les doubles slashes
    image_path = image_path.replace("//", "/")
    
    # 🧩 S'assurer que ça commence par uploads/ (une seule fois)
    if not image_path.startswith("uploads/"):
        image_path = f"uploads/{image_path}"

    # 🔗 Construire l'URL
    return f"http://localhost:8000/{image_path.lstrip('/')}"

# Ajoutez temporairement cette route pour déboguer
@router.get("/debug/{id_product}")
def debug_product(id_product: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id_product == id_product).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    return {
        "image_brut_bdd": product.image,  # ⬅️ Ce qui est en BDD
        "image_url_apres_traitement": get_image_url(product.image)  # ⬅️ Ce qui est retourné
    }

@router.get("/debug-images")
def debug_images(db: Session = Depends(get_db)):
    """Route temporaire pour debugger les chemins d'images"""
    products = db.query(models.Product).limit(5).all()
    
    debug_info = []
    for p in products:
        debug_info.append({
            "id_product": p.id_product,
            "nom": p.nom,
            "image_brute_bdd": p.image,
            "image_url_generee": get_image_url(p.image),
            "fichier_existe": os.path.exists(p.image.replace("\\", "/").lstrip("/")) if p.image and not p.image.startswith("http") else "URL externe"
        })
    
    return debug_info


# ==========================================================
# 🟢 AJOUT PRODUIT
# ==========================================================
@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# ==========================================================
# 🟢 LISTE DE TOUS LES PRODUITS (avec note et avis)
# ==========================================================
@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()

    results = []
    for p in products:
        # ⭐ Moyenne et nombre d'avis
        avg_note = (
            db.query(func.avg(models.ProductReview.note))
            .filter(models.ProductReview.id_product == p.id_product)
            .scalar()
        )
        nb_reviews = (
            db.query(func.count(models.ProductReview.id_review))
            .filter(models.ProductReview.id_product == p.id_product)
            .scalar()
        )

        # 🖼️ URL de l'image (gère URLs externes ET locales)
        p.image_url = get_image_url(p.image)
        p.note_moyenne = round(avg_note or 5, 2)
        p.nb_reviews = nb_reviews
        results.append(p)

    return results


# ==========================================================
# 🔍 RECHERCHE & FILTRAGE PRODUITS
# ==========================================================
@router.get("/search", response_model=list[ProductResponse], summary="Rechercher ou filtrer des produits")
def search_products(
    db: Session = Depends(get_db),
    q: str = Query(None, description="Mot clé à rechercher (nom ou description)"),
    category_id: int = Query(None, description="Filtrer par catégorie"),
    min_price: float = Query(None, description="Prix minimum"),
    max_price: float = Query(None, description="Prix maximum"),
):
    query = db.query(models.Product)

    # 🔎 Recherche plein texte
    if q:
        query = query.filter(
            or_(
                func.lower(models.Product.nom).like(f"%{q.lower()}%"),
                func.lower(models.Product.description).like(f"%{q.lower()}%")
            )
        )

    # 🎯 Filtres additionnels
    if category_id:
        query = query.filter(models.Product.id_category == category_id)
    if min_price is not None:
        query = query.filter(models.Product.prix >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.prix <= max_price)

    results = query.all()
    enriched_products = []

    for p in results:
        # ⭐ Notes et avis
        avg_note = (
            db.query(func.avg(models.ProductReview.note))
            .filter(models.ProductReview.id_product == p.id_product)
            .scalar()
        )
        nb_reviews = (
            db.query(func.count(models.ProductReview.id_review))
            .filter(models.ProductReview.id_product == p.id_product)
            .scalar()
        )

        # 🖼️ URL image (gère URLs externes ET locales)
        p.image_url = get_image_url(p.image)

        # 👤 Nom du vendeur
        p.vendeur_nom = f"{p.seller.prenom} {p.seller.nom}" if p.seller else None
        p.note_moyenne = round(avg_note or 5, 2)
        p.nb_reviews = nb_reviews

        enriched_products.append(p)

    return enriched_products


# ==========================================================
# 🟢 DÉTAIL D'UN PRODUIT AVEC VENDEUR + AVIS
# ==========================================================
@router.get("/{id_product}", response_model=ProductResponse)
def get_product(id_product: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id_product == id_product).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    # ⭐ Calcul des avis
    avg_note = (
        db.query(func.avg(models.ProductReview.note))
        .filter(models.ProductReview.id_product == id_product)
        .scalar()
    )
    nb_reviews = (
        db.query(func.count(models.ProductReview.id_review))
        .filter(models.ProductReview.id_product == id_product)
        .scalar()
    )

    # 👤 Nom du vendeur
    vendeur_nom = f"{product.seller.prenom} {product.seller.nom}" if product.seller else None

    # 🖼️ URL image (gère URLs externes ET locales)
    image_url = get_image_url(product.image)

    # Injection des infos supplémentaires
    product.note_moyenne = round(avg_note or 5, 2)
    product.nb_reviews = nb_reviews
    product.vendeur_nom = vendeur_nom
    product.image_url = image_url

    return product


# ==========================================================
# 🌍 PRODUITS PAR CATÉGORIE (accès public)
# ==========================================================
@router.get("/public/category/{id_category}", response_model=list[ProductResponse])
def list_products_by_category(id_category: int, db: Session = Depends(get_db)):
    products = db.query(models.Product).filter(models.Product.id_category == id_category).all()

    if not products:
        raise HTTPException(status_code=404, detail="Aucun produit trouvé dans cette catégorie.")

    for p in products:
        # ⭐ Notes
        avg_note = (
            db.query(func.avg(models.ProductReview.note))
            .filter(models.ProductReview.id_product == p.id_product)
            .scalar()
        )
        nb_reviews = (
            db.query(func.count(models.ProductReview.id_review))
            .filter(models.ProductReview.id_product == p.id_product)
            .scalar()
        )

        p.note_moyenne = round(avg_note or 5, 2)
        p.nb_reviews = nb_reviews

        # 🖼️ URL (gère URLs externes ET locales)
        p.image_url = get_image_url(p.image)

    return products