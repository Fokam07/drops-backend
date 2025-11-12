from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from fastapi.staticfiles import StaticFiles
from app.routes import (
    users,
    products,
    orders,
    auth,
    cart,
    payment,
    reviews,
    sellers,
    admin,
    admin_dashboard,
    seller_dashboard,
    categories,
)
from fastapi import Depends
from sqlalchemy import text
from app.database import get_db


# =====================================================
# ✅ Configuration FastAPI
# =====================================================
app = FastAPI(title="Drops API", version="1.1")

@app.get("/health/db")
def check_database_connection(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "✅ Database connected successfully!"}
    except Exception as e:
        return {"status": "❌ Database connection failed!", "error": str(e)}

# =====================================================
# 🌐 Middleware CORS (doit venir AVANT les routes)
# =====================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⬅️ accepte tout pour tester
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 📂 Montage du dossier d'uploads (pour les images produits)
# =====================================================
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# =====================================================
# ⚙️ Création des tables (après app)
# =====================================================
Base.metadata.create_all(bind=engine)

# =====================================================
# 🚀 Inclusion des routes
# =====================================================
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
app.include_router(payment.router, prefix="/api/payments", tags=["Payments"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(sellers.router, prefix="/api/sellers", tags=["Sellers"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin_dashboard.router, prefix="/api/admin", tags=["Admin Dashboard"])
app.include_router(seller_dashboard.router, prefix="/api/sellers", tags=["Seller Dashboard"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])

@app.get("/")
def root():
    return {"message": "Bienvenue sur Drops API 🚀"}
