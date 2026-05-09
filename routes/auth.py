from fastapi import APIRouter, HTTPException, Depends
from database import get_supabase
from models.auth import UserLogin, UserSignup, UserResponse
from auth.utils import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
async def signup(user_data: UserSignup):
    supabase = get_supabase()
    try:
        response = supabase.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True, # Bypass email confirmation
            "user_metadata": {
                "full_name": user_data.full_name,
                "role": user_data.role
            }
        })
        return {"message": "User created successfully", "user": response}
    except Exception as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait a minute before trying again."
            )
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user_data: UserLogin):
    supabase = get_supabase()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user": response.user
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid credentials")

@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    return user
