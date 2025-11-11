from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app import models
from app.utils.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import Form
from pydantic import BaseModel

router = APIRouter()

class LoginSchema(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(login_data: LoginSchema, db: Session = Depends(get_db)):
    """
    Login avec email/mot de passe via JSON
    """
    user = db.query(models.User).filter(models.User.email == login_data.email).first()

    # 🔍 Debug : email non trouvé
    if not user:
        print("🚫 Aucun utilisateur trouvé pour :", login_data.email)
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    print("\n=== 🔎 DEBUG LOGIN ===")
    print("Email reçu :", login_data.email)
    print("Mot de passe reçu :", login_data.password)
    print("Hash stocké :", user.mot_de_passe)

    # Vérification bcrypt
    from app.utils.security import verify_password
    result = verify_password(login_data.password, user.mot_de_passe)
    print("Résultat de verify_password:", result)

    if not result:
        print("❌ Le mot de passe ne correspond pas.")
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

    from datetime import timedelta
    from app.utils.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

    token_data = {"sub": str(user.id_user)}
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    print("✅ Connexion réussie :", user.email)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id_user,
            "nom": user.nom,
            "prenom": user.prenom,
            "email": user.email,
            "role": user.role
        }
    }
