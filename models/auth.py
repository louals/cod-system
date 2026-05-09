from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Literal["user", "admin"] = "user"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
