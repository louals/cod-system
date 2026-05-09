from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class OrderItemBase(BaseModel):
    product_id: str
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: str
    order_id: str
    price_at_purchase: float

class OrderBase(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    customer_city: str
    user_id: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "shipped", "delivered", "cancelled", "returned"]

class Order(OrderBase):
    id: str
    total_price: float
    status: str
    created_at: datetime
    items: List[OrderItem] = []
