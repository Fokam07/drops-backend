from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas.user_schema import UserCreate, UserResponse
from app.utils.security import get_current_user, require_role
from passlib.context import CryptContext
import bcrypt

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ======================================================
# 🔐 Fonction sécurisée de hash de mot de passe
# ======================================================
def hash_password(password: str):
    """
    Hash un mot de passe en contournant la limite de 72 bytes
    """
    password_bytes = password.encode('utf-8')
    
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Utiliser bcrypt directement
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

# ======================================================
# 👤 1️⃣ - Inscription d’un CLIENT (publique)
# ======================================================
@router.post("/register", response_model=UserResponse, summary="Inscription client")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        print("📩 Requête reçue :", user.dict())

        # Vérifie si l'email existe déjà
        existing_user = db.query(models.User).filter(models.User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Cet email existe déjà.")

        # Hash sécurisé
        hashed_pw = hash_password(user.mot_de_passe)

        # Création de l'utilisateur client
        new_user = models.User(
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            mot_de_passe=hashed_pw,
            role="CLIENT"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print("✅ Utilisateur créé :", new_user.id_user)
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERREUR SERVEUR :", e)
        raise HTTPException(status_code=500, detail=str(e))

# ======================================================
# 👑 2️⃣ - Création d’un utilisateur par ADMIN
# ======================================================
@router.post("/admin/create", response_model=UserResponse, summary="Création d’un utilisateur (ADMIN)")
def create_user_admin(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    require_role(current_user, ["ADMIN"])  # ✅ seul l’admin peut accéder

    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Cet email existe déjà.")

    # ✅ Vérification du rôle
    if user.role not in ["CLIENT", "VENDEUR", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Rôle invalide")

    hashed_pw = hash_password(user.mot_de_passe)
    new_user = models.User(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        mot_de_passe=hashed_pw,
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# ======================================================
# 👥 3️⃣ - Lister les utilisateurs
# ======================================================
@router.get("/", response_model=list[UserResponse], summary="Lister tous les utilisateurs")
def get_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_role(current_user, ["ADMIN"])
    return db.query(models.User).all()
