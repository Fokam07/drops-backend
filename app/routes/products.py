from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app import models
from app.schemas.product_schema import ProductCreate, ProductResponse
from app.utils.images import get_image_url

router = APIRouter(tags=["Products"])


# ==========================================================
# 🔧 ROUTES DEBUG (doivent être AVANT TOUTES LES DYNAMIQUES)
# ==========================================================

@router.get("/debug-images")
def debug_images(db: Session = Depends(get_db)):
    """
    Debug visuel : montre les chemins en BDD et les URLs générées.
    """
    products = db.query(models.Product).limit(15).all()

    data = []
    for p in products:
        data.append({
            "id_product": p.id_product,
            "nom": p.nom,
            "image_bdd": p.image,
            "image_url": get_image_url(p.image)
        })

    return data


@router.get("/debug/{id_product}")
def debug_single(id_product: int, db: Session = Depends(get_db)):
    """
    Debug un seul produit : utile pour voir si un chemin est cassé
    """
    p = db.query(models.Product).filter(models.Product.id_product == id_product).first()
    if not p:
        raise HTTPException(404, "Produit introuvable")

    return {
        "image_bdd": p.image,
        "image_url": get_image_url(p.image)
    }


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
# 🟢 LISTE DE TOUS LES PRODUITS
# ==========================================================
@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    results = []

    for p in products:
        avg = db.query(func.avg(models.ProductReview.note)).filter(
            models.ProductReview.id_product == p.id_product
        ).scalar()

        count = db.query(func.count(models.ProductReview.id_review)).filter(
            models.ProductReview.id_product == p.id_product
        ).scalar()

        p.image_url = get_image_url(p.image)
        p.note_moyenne = round(avg or 5, 2)
        p.nb_reviews = count

        results.append(p)

    return results


# ==========================================================
# 🔍 RECHERCHE & FILTRAGE
# ==========================================================
@router.get("/search", response_model=list[ProductResponse])
def search_products(
    db: Session = Depends(get_db),
    q: str = Query(None),
    category_id: int = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
):
    query = db.query(models.Product)

    if q:
        query = query.filter(
            or_(
                func.lower(models.Product.nom).like(f"%{q.lower()}%"),
                func.lower(models.Product.description).like(f"%{q.lower()}%")
            )
        )

    if category_id:
        query = query.filter(models.Product.id_category == category_id)

    if min_price is not None:
        query = query.filter(models.Product.prix >= min_price)

    if max_price is not None:
        query = query.filter(models.Product.prix <= max_price)

    products = query.all()
    results = []

    for p in products:
        avg = db.query(func.avg(models.ProductReview.note)).filter(
            models.ProductReview.id_product == p.id_product
        ).scalar()

        count = db.query(func.count(models.ProductReview.id_review)).filter(
            models.ProductReview.id_product == p.id_product
        ).scalar()

        p.image_url = get_image_url(p.image)
        p.note_moyenne = round(avg or 5, 2)
        p.nb_reviews = count
        p.vendeur_nom = f"{p.seller.prenom} {p.seller.nom}" if p.seller else None

        results.append(p)

    return results


# ==========================================================
# 🌍 PRODUITS PAR CATÉGORIE
# ==========================================================
@router.get("/public/category/{id_category}", response_model=list[ProductResponse])
def list_products_by_category(id_category: int, db: Session = Depends(get_db)):

    products = db.query(models.Product).filter(
        models.Product.id_category == id_category
    ).all()

    if not products:
        raise HTTPException(404, "Aucun produit trouvé dans cette catégorie")

    for p in products:
        avg = db.query(func.avg(models.ProductReview.note)).filter(
            models.ProductReview.id_product == p.id_product
        ).scalar()

        count = db.query(func.count(models.ProductReview.id_review)).filter(
            models.ProductReview.id_product == p.id_product
        ).scalar()

        p.image_url = get_image_url(p.image)
        p.note_moyenne = round(avg or 5, 2)
        p.nb_reviews = count

    return products


# ==========================================================
# 🟢 DETAIL PRODUIT (À METTRE EN DERNIER !)
# ==========================================================
@router.get("/{id_product}", response_model=ProductResponse)
def get_product(id_product: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id_product == id_product).first()

    if not p:
        raise HTTPException(404, "Produit non trouvé")

    avg = db.query(func.avg(models.ProductReview.note)).filter(
        models.ProductReview.id_product == id_product
    ).scalar()

    count = db.query(func.count(models.ProductReview.id_review)).filter(
        models.ProductReview.id_product == id_product
    ).scalar()

    p.image_url = get_image_url(p.image)
    p.note_moyenne = round(avg or 5, 2)
    p.nb_reviews = count
    p.vendeur_nom = f"{p.seller.prenom} {p.seller.nom}" if p.seller else None

    return p

