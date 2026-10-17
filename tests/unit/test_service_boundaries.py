from unittest.mock import MagicMock

import pytest

from app.features.inventory.schemas import ReserveStockRequest
from app.features.inventory.service import (
    InventoryService,
    InventoryServiceInterface,
)
from app.features.orders.schemas import OrderCreateRequest
from app.features.orders.service import (
    OrderService,
    OrderServiceInterface,
)


@pytest.mark.unit
def test_order_service_boundary_conformance():
    service = OrderService()
    assert isinstance(service, OrderServiceInterface)

    mock_db = MagicMock()
    mock_request = OrderCreateRequest(
        customer_id="cust_1",
        currency="USD",
        items=[{"sku": "SKU-1", "quantity": 1, "unit_price": "10.00"}],
    )

    with pytest.raises(NotImplementedError) as exc_info:
        service.create_order_with_reservation(db=mock_db, request=mock_request)
    assert "must be implemented by the engineer" in str(exc_info.value)


@pytest.mark.unit
def test_inventory_service_boundary_conformance():
    service = InventoryService()
    assert isinstance(service, InventoryServiceInterface)

    mock_db = MagicMock()
    mock_request = ReserveStockRequest(
        order_reference="ORD-1",
        items=[{"sku": "SKU-1", "quantity": 1}],
    )

    with pytest.raises(NotImplementedError) as exc_info:
        service.reserve_stock_atomic(db=mock_db, request=mock_request)
    assert "must be implemented by the engineer" in str(exc_info.value)
