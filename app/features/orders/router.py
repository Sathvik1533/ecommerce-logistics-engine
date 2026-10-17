from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.orders.schemas import OrderCreateRequest, OrderResponse
from app.features.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


# Dependency provider for OrderService to support easy test stubbing / mocking
def get_order_service() -> OrderService:
    return OrderService()


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Order with Atomic Inventory Reservation",
    description=(
        "Validates order details, reserves required inventory items within a "
        "transactional boundary, creates the order, and dispatches background fulfillment tasks."
    ),
)
def create_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        order = service.create_order_with_reservation(db=db, request=request)
        return OrderResponse.model_validate(order)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc


@router.get(
    "/{order_reference}",
    response_model=OrderResponse,
    summary="Get Order Details by Reference",
)
def get_order(
    order_reference: str,
    db: Session = Depends(get_db),
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        order = service.get_order_by_reference(db=db, order_reference=order_reference)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with reference '{order_reference}' not found",
            )
        return OrderResponse.model_validate(order)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
