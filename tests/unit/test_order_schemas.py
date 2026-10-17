from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.features.orders.schemas import OrderCreateRequest, OrderItemCreate


@pytest.mark.unit
def test_order_create_request_valid():
    payload = {
        "customer_id": "cust_12345",
        "currency": "USD",
        "items": [
            {"sku": "SKU-IPHONE15-BLK", "quantity": 2, "unit_price": "899.99"},
            {"sku": "SKU-CASE-CLR", "quantity": 1, "unit_price": "29.99"},
        ],
    }
    request = OrderCreateRequest.model_validate(payload)
    assert request.customer_id == "cust_12345"
    assert len(request.items) == 2
    assert request.items[0].sku == "SKU-IPHONE15-BLK"
    assert request.items[0].quantity == 2
    assert request.items[0].unit_price == Decimal("899.99")


@pytest.mark.unit
def test_order_item_invalid_quantity():
    with pytest.raises(ValidationError):
        OrderItemCreate(sku="SKU-TEST", quantity=0, unit_price=Decimal("10.00"))

    with pytest.raises(ValidationError):
        OrderItemCreate(sku="SKU-TEST", quantity=-5, unit_price=Decimal("10.00"))


@pytest.mark.unit
def test_order_empty_items_validation_fails():
    with pytest.raises(ValidationError):
        OrderCreateRequest(customer_id="cust_123", currency="USD", items=[])
