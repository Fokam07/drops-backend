from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.utils.security import get_current_user, require_role
from sqlalchemy import func
from datetime import datetime

router = APIRouter(tags=["Reviews"])




#  ------------------------------------
# 💬 Ajouter ou mettre à jour un avis
# ------------------------------------
@router.post("/{id_product}", summary="Ajouter ou modifier un avis sur un produit (client)")
def add_or_update_review(
    id_product: int,
    review: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    require_role(user, ["CLIENT"])

    product = db.query(models.Product).filter(models.Product.id_product == id_product).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    existing = db.query(models.ProductReview).filter(
        models.ProductReview.id_user == user.id_user,
        models.ProductReview.id_product == id_product
    ).first()

    if existing:
        existing.note = review.get("note", 5)
        existing.commentaire = review.get("commentaire", "")
        existing.date_review = datetime.now()
        db.commit()
        db.refresh(existing)
        message = "Avis mis à jour avec succès ✅"
        review_obj = existing
    else:
        new_review = models.ProductReview(
            id_user=user.id_user,
            id_product=id_product,
            commentaire=review.get("commentaire", ""),
            note=review.get("note", 5)
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        message = "Avis ajouté avec succès ✅"
        review_obj = new_review

    avg_note = (
        db.query(func.avg(models.ProductReview.note))
        .filter(models.ProductReview.id_product == id_product)
        .scalar()
    )
    product.note_moyenne = round(avg_note or 5, 2)
    db.commit()

    return {
        "message": message,
        "note_moyenne": product.note_moyenne,
        "review": {
            "id_review": review_obj.id_review,
            "note": review_obj.note,
            "commentaire": review_obj.commentaire,
            "date_review": review_obj.date_review
        }
    }


# ------------------------------------
# 🌍 Lister les avis d’un produit
# ------------------------------------
@router.get("/product/{id_product}", summary="Lister les avis d’un produit (public)")
def list_product_reviews(id_product: int, db: Session = Depends(get_db)):
    print("🧩 DEBUG — ID produit reçu :", id_product)  # ✅ ICI, à l’intérieur de la fonction

    product = db.query(models.Product).filter(models.Product.id_product == id_product).first()
    print("📦 DEBUG — Produit trouvé :", product)

    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    reviews = db.query(models.ProductReview).filter(models.ProductReview.id_product == id_product).all()

    average_note = (
        db.query(func.avg(models.ProductReview.note))
        .filter(models.ProductReview.id_product == id_product)
        .scalar()
    )

    return {
        "produit": product.nom,
        "note_moyenne": round(average_note or 5, 2),
        "nombre_avis": len(reviews),
        "avis": [
            {
                "note": r.note,
                "commentaire": r.commentaire,
                "auteur": r.id_user,
                "date": r.date_review
            } for r in reviews
        ]
    }