from pydantic import BaseModel, ConfigDict, Field


class StockCheckRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64, description="Stock Keeping Unit")
    quantity_needed: int = Field(..., gt=0, description="Quantity required")


class ReservationItemRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(..., gt=0)


class ReserveStockRequest(BaseModel):
    order_reference: str = Field(..., min_length=1, max_length=64)
    items: list[ReservationItemRequest] = Field(..., min_length=1)


class ReservationItemResult(BaseModel):
    sku: str
    quantity: int
    warehouse_code: str
    success: bool


class ReservationResult(BaseModel):
    order_reference: str
    all_reserved: bool
    reservations: list[ReservationItemResult] = []


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    warehouse_code: str
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
