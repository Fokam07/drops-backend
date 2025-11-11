from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from app.database import get_db
from app import models
from app.utils.security import get_current_user, require_role

router = APIRouter()

@router.get("/dashboard", summary="Bilan complet du vendeur connecté")
def seller_dashboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_role(user, ["VENDEUR"])

    # 🛍️ Nombre total de produits
    total_products = db.query(func.count(models.Product.id_product)).filter(
        models.Product.id_seller == user.id_user
    ).scalar()

    # 🧾 Total commandes associées à ses produits
    total_orders = (
        db.query(func.count(models.OrderItem.id_order_item))
        .join(models.Product, models.OrderItem.id_product == models.Product.id_product)
        .filter(models.Product.id_seller == user.id_user)
        .scalar()
    )

    # 💰 Total revenus
    total_revenue = (
        db.query(func.sum(models.OrderItem.prix_unitaire * models.OrderItem.quantite))
        .join(models.Product, models.OrderItem.id_product == models.Product.id_product)
        .filter(models.Product.id_seller == user.id_user)
        .scalar() or 0
    )

    # ⭐ Note moyenne globale sur ses produits
    avg_rating = (
        db.query(func.avg(models.Review.note))
        .join(models.Product, models.Review.id_product == models.Product.id_product)
        .filter(models.Product.id_seller == user.id_user)
        .scalar()
    )
    avg_rating = round(avg_rating or 0, 2)

    # 📅 Commandes par jour (7 derniers jours)
    start_date = datetime.utcnow() - timedelta(days=7)
    orders_by_day = (
        db.query(
            cast(models.Order.date_commande, Date).label("jour"),
            func.count(models.Order.id_order).label("nb_commandes")
        )
        .join(models.OrderItem, models.Order.id_order == models.OrderItem.id_order)
        .join(models.Product, models.OrderItem.id_product == models.Product.id_product)
        .filter(models.Product.id_seller == user.id_user)
        .filter(models.Order.date_commande >= start_date)
        .group_by(cast(models.Order.date_commande, Date))
        .order_by("jour")
        .all()
    )

    return {
        "vendeur": f"{user.prenom} {user.nom}",
        "produits": total_products,
        "commandes_total": total_orders,
        "revenus_totaux": float(total_revenue),
        "note_moyenne": avg_rating,
        "commandes_par_jour": [
            {"date": str(row.jour), "nombre": row.nb_commandes} for row in orders_by_day
        ]
    }
