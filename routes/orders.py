from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from auth.utils import get_current_user, get_supabase, get_admin_user
from models.order import Order, OrderCreate, OrderStatusUpdate
from postgrest.exceptions import APIError
from supabase import Client

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=Order)
async def place_order(
    order_data: OrderCreate, 
    current_user = Depends(get_current_user)
):
    supabase = get_supabase()
    try:
        # 1. Calculate total price and verify stock
        total_price = 0
        product_details = []
        
        for item in order_data.items:
            prod_resp = supabase.table("products").select("*").eq("id", item.product_id).execute()
            if not prod_resp.data:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            product = prod_resp.data[0]
            if product["stock"] < item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['name']}")
            
            total_price += product["price"] * item.quantity
            product_details.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price_at_purchase": product["price"]
            })

        # 2. Create the order
        order_dict = order_data.model_dump(exclude={"items"})
        order_dict["total_price"] = total_price
        order_dict["status"] = "pending"
        order_dict["user_id"] = current_user.id 
        
        order_resp = supabase.table("orders").insert(order_dict).execute()
        if not order_resp.data:
            raise HTTPException(status_code=400, detail="Failed to create order")
        
        new_order = order_resp.data[0]
        
        # 3. Create order items
        final_items = []
        for detail in product_details:
            detail["order_id"] = new_order["id"]
            item_resp = supabase.table("order_items").insert(detail).execute()
            if item_resp.data:
                final_items.append(item_resp.data[0])
            
            # Update stock
            current_stock = supabase.table("products").select("stock").eq("id", detail["product_id"]).execute().data[0]["stock"]
            supabase.table("products").update({"stock": current_stock - detail["quantity"]}).eq("id", detail["product_id"]).execute()

        return {**new_order, "items": final_items}
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[Order])
async def get_orders(current_user = Depends(get_current_user)):
    """Users see their own orders; Admins see all orders."""
    supabase = get_supabase()
    try:
        user_role = current_user.user_metadata.get("role", "user")
        
        if user_role == "admin":
            response = supabase.table("orders").select("*").execute()
        else:
            response = supabase.table("orders").select("*").eq("user_id", current_user.id).execute()
        
        orders = response.data
        for order in orders:
            items_resp = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute()
            order["items"] = items_resp.data
            
        return orders
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: str, current_user = Depends(get_current_user)):
    supabase = get_supabase()
    try:
        order_resp = supabase.table("orders").select("*").eq("id", order_id).execute()
        
        if not order_resp.data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = order_resp.data[0]
        
        # Security check: owner or admin
        user_role = current_user.user_metadata.get("role", "user")
        if order.get("user_id") != current_user.id and user_role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
        
        items_resp = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
        order["items"] = items_resp.data
        return order
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: str, 
    status_data: OrderStatusUpdate,
    admin = Depends(get_admin_user)
):
    """Only admins can update order statuses."""
    supabase = get_supabase()
    try:
        # 1. Verify order exists
        order_resp = supabase.table("orders").select("*").eq("id", order_id).execute()
        if not order_resp.data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        old_order = order_resp.data[0]
        new_status = status_data.status
        
        # 2. Update status
        update_resp = supabase.table("orders").update({"status": new_status}).eq("id", order_id).execute()
        
        # 3. Handle stock restoration/deduction logic...
        if new_status in ["cancelled", "returned"] and old_order["status"] not in ["cancelled", "returned"]:
            items_resp = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
            for item in items_resp.data:
                prod_data = supabase.table("products").select("stock").eq("id", item["product_id"]).execute()
                if prod_data.data:
                    current_stock = prod_data.data[0]["stock"]
                    supabase.table("products").update({"stock": current_stock + item["quantity"]}).eq("id", item["product_id"]).execute()
        
        elif old_order["status"] in ["cancelled", "returned"] and new_status not in ["cancelled", "returned"]:
            items_resp = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
            for item in items_resp.data:
                prod_data = supabase.table("products").select("stock").eq("id", item["product_id"]).execute()
                if prod_data.data:
                    current_stock = prod_data.data[0]["stock"]
                    supabase.table("products").update({"stock": current_stock - item["quantity"]}).eq("id", item["product_id"]).execute()

        updated_order = update_resp.data[0]
        items_resp = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
        updated_order["items"] = items_resp.data
        return updated_order
        
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, current_user = Depends(get_current_user)):
    supabase = get_supabase()
    try:
        order_resp = supabase.table("orders").select("*").eq("id", order_id).execute()
        if not order_resp.data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = order_resp.data[0]
        if order.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this order")
        
        if order["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Cannot cancel order in {order['status']} status")
        
        # Bypass admin check for self-cancellation
        return await update_order_status(order_id, OrderStatusUpdate(status="cancelled"), admin=current_user)
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
