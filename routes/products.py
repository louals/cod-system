from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from auth.utils import get_supabase, get_admin_user
from models.product import Product, ProductCreate
from postgrest.exceptions import APIError

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    supabase = get_supabase()
    try:
        query = supabase.table("products").select("*")
        
        if category:
            query = query.eq("category", category)
        if search:
            query = query.ilike("name", f"%{search}%")
        if min_price is not None:
            query = query.gte("price", min_price)
        if max_price is not None:
            query = query.lte("price", max_price)
            
        response = query.execute()
        return response.data
    except APIError as e:
        if e.code == "PGRST205":
            raise HTTPException(status_code=503, detail="Database table 'products' not found. Please run setup.sql in Supabase.")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    supabase = get_supabase()
    try:
        response = supabase.table("products").select("*").eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return response.data[0]
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("", response_model=Product)
async def create_product(product: ProductCreate, admin = Depends(get_admin_user)):
    """Only admins can create products."""
    supabase = get_supabase()
    try:
        response = supabase.table("products").insert(product.model_dump()).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create product")
        return response.data[0]
    except APIError as e:
        if e.code == "PGRST205":
            raise HTTPException(status_code=503, detail="Database table 'products' not found. Please run setup.sql in Supabase.")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
