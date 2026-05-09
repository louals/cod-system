from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    File,
    UploadFile,
    Form
)

from typing import List, Optional, Annotated

from auth.utils import get_supabase, get_admin_user
from models.product import Product
from postgrest.exceptions import APIError
from utils.cloudinary_utils import upload_image

import json

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

# =========================
# GET ALL PRODUCTS
# =========================
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
            raise HTTPException(
                status_code=503,
                detail="Database table 'products' not found."
            )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =========================
# GET SINGLE PRODUCT
# =========================
@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    supabase = get_supabase()

    try:
        response = (
            supabase
            .table("products")
            .select("*")
            .eq("id", product_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return response.data[0]

    except APIError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =========================
# CREATE PRODUCT
# =========================
@router.post("", response_model=Product)
async def create_product(
    images: Annotated[
        List[UploadFile],
        File(description="Upload multiple product images")
    ],

    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),

    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),

    admin=Depends(get_admin_user)
):
    """
    Only admins can create products.
    Supports multiple image uploads.
    """

    supabase = get_supabase()

    try:
        image_urls = []

        # Upload all images
        for image in images:

            # Read image bytes
            content = await image.read()

            # Upload to cloudinary
            url = upload_image(
                content,
                image.filename
            )

            image_urls.append(url)

        # Product data
        product_data = {
            "name": name,
            "description": description,
            "price": price,
            "stock": stock,
            "category": category,
            "images": image_urls
        }

        # Insert into DB
        response = (
            supabase
            .table("products")
            .insert(product_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=400,
                detail="Failed to create product"
            )

        return response.data[0]

    except APIError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


# =========================
# UPDATE PRODUCT
# =========================
@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str,

    new_images: Annotated[
        Optional[List[UploadFile]],
        File(description="Upload new product images")
    ] = None,

    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    category: Optional[str] = Form(None),

    existing_images: Optional[str] = Form(None),

    admin=Depends(get_admin_user)
):
    """
    Update product details.
    Can keep existing images and add new ones.
    """

    supabase = get_supabase()

    try:

        update_data = {}

        # Update fields only if provided
        if name is not None:
            update_data["name"] = name

        if description is not None:
            update_data["description"] = description

        if price is not None:
            update_data["price"] = price

        if stock is not None:
            update_data["stock"] = stock

        if category is not None:
            update_data["category"] = category

        # =========================
        # HANDLE EXISTING IMAGES
        # =========================
        final_images = []

        if existing_images:
            try:
                final_images = json.loads(existing_images)

                if not isinstance(final_images, list):
                    raise ValueError()

            except:
                raise HTTPException(
                    status_code=400,
                    detail="existing_images must be a valid JSON list"
                )

        # =========================
        # HANDLE NEW IMAGES
        # =========================
        if new_images:

            for image in new_images:

                if image.filename:

                    content = await image.read()

                    url = upload_image(
                        content,
                        image.filename
                    )

                    final_images.append(url)

        # Save images
        update_data["images"] = final_images

        # =========================
        # UPDATE DATABASE
        # =========================
        response = (
            supabase
            .table("products")
            .update(update_data)
            .eq("id", product_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return response.data[0]

    except APIError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# DELETE PRODUCT
# =========================
@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    admin=Depends(get_admin_user)
):
    """
    Delete a product.
    """

    supabase = get_supabase()

    try:
        response = (
            supabase
            .table("products")
            .delete()
            .eq("id", product_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return {
            "message": "Product deleted successfully"
        }

    except APIError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )