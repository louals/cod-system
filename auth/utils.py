from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from config import settings
from gotrue.errors import AuthApiError

security = HTTPBearer()

def get_supabase() -> Client:
    """Returns a Supabase client using the Service Role key to bypass RLS."""
    return create_client(settings.supabase_url, settings.supabase_key)

def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)):
    supabase = get_supabase()
    try:
        user_resp = supabase.auth.get_user(auth.credentials)
        if not user_resp or not user_resp.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_resp.user
    except AuthApiError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

def get_admin_user(current_user = Depends(get_current_user)):
    """Dependency that ensures the user has an 'admin' role in their metadata."""
    # Supabase stores custom data in user_metadata
    user_role = current_user.user_metadata.get("role", "user")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action"
        )
    return current_user
