from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

# 🔑 Clé secrète (à placer dans .env plus tard)
SECRET_KEY = "DROPS_SECRET_KEY_123456"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ⚙️ Contexte de hachage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==================================================
# 🔐 FONCTIONS UTILITAIRES
# ==================================================
def hash_password(password: str):
    """Hash du mot de passe sécurisé avec coupure à 72 bytes"""
    encoded_pw = password.encode("utf-8")
    if len(encoded_pw) > 72:
        encoded_pw = encoded_pw[:72]
        password = encoded_pw.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """Vérifie le mot de passe (retourne False si invalides)"""
    try:
        print("🧩 DEBUG - Mot de passe en clair:", plain_password)
        print("🧩 DEBUG - Hash stocké:", hashed_password)
        result = pwd_context.verify(plain_password, hashed_password)
        print("✅ Résultat vérification:", result)
        return result
    except Exception as e:
        print("❌ Erreur de vérification bcrypt :", e)
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Crée un token JWT avec expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Récupère l'utilisateur courant depuis le token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id_user == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(user, allowed_roles: list[str]):
    """Vérifie les rôles autorisés"""
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Accès refusé")
