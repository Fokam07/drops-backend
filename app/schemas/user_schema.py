from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str = Field(..., min_length=6, max_length=72)
    role: Optional[str] = "CLIENT"

class UserResponse(BaseModel):
    id_user: int
    nom: str
    prenom: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True
