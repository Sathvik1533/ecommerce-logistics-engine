from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.features.orders.models import OrderStatus


class OrderItemCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64, description="Stock Keeping Unit identifier")
    quantity: int = Field(..., gt=0, description="Quantity to purchase, must be positive")
    unit_price: Decimal = Field(
        ..., gt=0, decimal_places=2, description="Price per unit in currency"
    )


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    quantity: int
    unit_price: Decimal


class OrderCreateRequest(BaseModel):
    customer_id: str = Field(
        ..., min_length=1, max_length=64, description="Customer unique identifier"
    )
    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="ISO 4217 Currency Code"
    )
    items: list[OrderItemCreate] = Field(
        ..., min_length=1, description="List of order items to purchase"
    )


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_reference: str
    customer_id: str
    status: OrderStatus
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []
