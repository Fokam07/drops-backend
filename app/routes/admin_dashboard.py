from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import models
from app.utils.security import get_current_user, require_role
from datetime import datetime, timedelta
from sqlalchemy import func, cast, Date

router = APIRouter()

@router.get("/dashboard", summary="Statistiques globales du site (Admin uniquement)")
def admin_dashboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_role(user, ["ADMIN"])

    # 👥 Comptes
    total_users = db.query(func.count(models.User.id_user)).scalar()
    total_vendeurs = db.query(func.count(models.User.id_user)).filter(models.User.role == "VENDEUR").scalar()
    total_clients = db.query(func.count(models.User.id_user)).filter(models.User.role == "CLIENT").scalar()

    # 🛍️ Produits
    total_products = db.query(func.count(models.Product.id_product)).scalar()

    # 🧾 Commandes
    total_orders = db.query(func.count(models.Order.id_order)).scalar()
    orders_by_status = (
        db.query(models.Order.statut, func.count(models.Order.id_order))
        .group_by(models.Order.statut)
        .all()
    )
    order_stats = {status: count for status, count in orders_by_status}

    # 💰 Paiements
    total_payments = db.query(func.count(models.Payment.id_payment)).scalar()
    successful_payments = db.query(func.count(models.Payment.id_payment)).filter(models.Payment.statut == "SUCCES").scalar()
    total_revenue = db.query(func.sum(models.Payment.montant)).filter(models.Payment.statut == "SUCCES").scalar() or 0

    # 🕒 Activité
    last_order = db.query(func.max(models.Order.date_commande)).scalar()
    last_payment = db.query(func.max(models.Payment.date_paiement)).scalar()

    return {
        "utilisateurs": {
            "total": total_users,
            "vendeurs": total_vendeurs,
            "clients": total_clients
        },
        "produits": {
            "total": total_products
        },
        "commandes": {
            "total": total_orders,
            "par_statut": order_stats
        },
        "paiements": {
            "total": total_payments,
            "reussis": successful_payments,
            "revenus_totaux": float(total_revenue)
        },
        "activite": {
            "derniere_commande": str(last_order) if last_order else None,
            "dernier_paiement": str(last_payment) if last_payment else None
        }
    }

# ----------------------------------------------------------
# 📆 Statistiques journalières (commandes, paiements, revenus)
# ----------------------------------------------------------
@router.get("/dashboard/daily", summary="Statistiques journalières (Admin uniquement)")
def daily_stats(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    days: int = 30
):
    require_role(user, ["ADMIN"])

    # Déterminer la date de début
    start_date = datetime.utcnow() - timedelta(days=days)

    # 📦 Commandes par jour
    orders_data = (
        db.query(
            cast(models.Order.date_commande, Date).label("jour"),
            func.count(models.Order.id_order).label("total_commandes")
        )
        .filter(models.Order.date_commande >= start_date)
        .group_by(cast(models.Order.date_commande, Date))
        .order_by("jour")
        .all()
    )

    # 💰 Paiements réussis par jour
    payments_data = (
        db.query(
            cast(models.Payment.date_paiement, Date).label("jour"),
            func.count(models.Payment.id_payment).label("paiements_reussis"),
            func.sum(models.Payment.montant).label("revenus_totaux")
        )
        .filter(models.Payment.date_paiement >= start_date)
        .filter(models.Payment.statut == "SUCCES")
        .group_by(cast(models.Payment.date_paiement, Date))
        .order_by("jour")
        .all()
    )

    # Convertir les résultats en dictionnaires
    orders_stats = [
        {"date": str(row.jour), "total_commandes": row.total_commandes}
        for row in orders_data
    ]

    payments_stats = [
        {
            "date": str(row.jour),
            "paiements_reussis": row.paiements_reussis,
            "revenus_totaux": float(row.revenus_totaux or 0)
        }
        for row in payments_data
    ]

    return {
        "periode": f"Derniers {days} jours",
        "commandes_par_jour": orders_stats,
        "paiements_par_jour": payments_stats
    }
