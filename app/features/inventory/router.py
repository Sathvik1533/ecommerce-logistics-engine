from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.inventory.schemas import (
    ReservationResult,
    ReserveStockRequest,
)
from app.features.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def get_inventory_service() -> InventoryService:
    return InventoryService()


@router.get(
    "/availability",
    summary="Check SKU Availability",
    description="Check whether a specific quantity of SKU is available for reservation.",
)
def check_sku_availability(
    sku: str = Query(..., description="Stock Keeping Unit"),
    quantity: int = Query(..., gt=0, description="Quantity required"),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> dict[str, object]:
    try:
        available = service.check_availability(db=db, sku=sku, quantity_needed=quantity)
        return {"sku": sku, "quantity_needed": quantity, "available": available}
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc


@router.post(
    "/reserve",
    response_model=ReservationResult,
    status_code=status.HTTP_200_OK,
    summary="Atomically Reserve Stock",
    description="Reserve warehouse inventory items atomically using row-level locking.",
)
def reserve_stock(
    request: ReserveStockRequest,
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> ReservationResult:
    try:
        return service.reserve_stock_atomic(db=db, request=request)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
