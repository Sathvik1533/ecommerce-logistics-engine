import pytest
from pydantic import ValidationError

from app.features.inventory.schemas import (
    ReservationItemRequest,
    ReserveStockRequest,
    StockCheckRequest,
)


@pytest.mark.unit
def test_stock_check_request_validation():
    req = StockCheckRequest(sku="SKU-SHOES-42", quantity_needed=5)
    assert req.sku == "SKU-SHOES-42"
    assert req.quantity_needed == 5

    with pytest.raises(ValidationError):
        StockCheckRequest(sku="SKU-SHOES-42", quantity_needed=0)


@pytest.mark.unit
def test_reserve_stock_request_valid():
    payload = {
        "order_reference": "ORD-2026-X89",
        "items": [
            {"sku": "SKU-LAPTOP-PRO", "quantity": 1},
            {"sku": "SKU-MOUSE-WL", "quantity": 2},
        ],
    }
    request = ReserveStockRequest.model_validate(payload)
    assert request.order_reference == "ORD-2026-X89"
    assert len(request.items) == 2


@pytest.mark.unit
def test_reservation_item_invalid_quantity():
    with pytest.raises(ValidationError):
        ReservationItemRequest(sku="SKU-LAPTOP-PRO", quantity=-1)
