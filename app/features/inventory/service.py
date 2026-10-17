"""
Inventory Feature Service Boundary.

Architectural Notice:
This module defines the service interface for stock allocation and inventory checks.
Core concurrency protection (pessimistic row locking with SELECT ... FOR UPDATE or optimistic
version checks), transactional isolation, and warehouse allocation algorithms will be
personally implemented by the backend engineer.
"""

from typing import Protocol, runtime_checkable

from sqlalchemy.orm import Session

from app.features.inventory.schemas import ReservationResult, ReserveStockRequest


@runtime_checkable
class InventoryServiceInterface(Protocol):
    """Interface defining inventory operations and reservation boundaries."""

    def check_availability(self, db: Session, sku: str, quantity_needed: int) -> bool:
        """Checks whether sufficient inventory is unreserved and available."""
        ...

    def reserve_stock_atomic(self, db: Session, request: ReserveStockRequest) -> ReservationResult:
        """
        Atomically reserves inventory for an order across one or multiple SKUs.

        Concurrency & Integrity Requirements:
        - Must acquire row-level locks on the target SKUs (e.g., `SELECT ... FOR UPDATE`)
          to prevent race conditions / overselling when concurrent checkouts hit identical items.
        - Must sort requested SKUs predictably before locking to avert deadlocks.
        - Must verify `total_quantity - reserved_quantity >= requested_quantity` under lock.
        - Must register `StockAllocation` records and increment `reserved_quantity`.
        - Rolls back or raises domain exceptions if any item cannot be satisfied.
        """
        ...

    def release_reservation(self, db: Session, order_reference: str) -> None:
        """Releases all reserved stock for an order (e.g. upon order cancellation or timeout)."""
        ...


class InventoryService:
    """Default implementation scaffold for Inventory business capability."""

    def check_availability(self, db: Session, sku: str, quantity_needed: int) -> bool:
        """
        Scaffolded stock availability check.
        """
        # TODO [Engineer Implementation]:
        # Query inventory item and evaluate available_quantity >= quantity_needed.
        raise NotImplementedError("Inventory check must be implemented by the engineer.")

    def reserve_stock_atomic(self, db: Session, request: ReserveStockRequest) -> ReservationResult:
        """
        Scaffolded atomic reservation with row-level locking.
        """
        # TODO [Engineer Implementation]:
        # 1. Sort SKUs to prevent database deadlocks across concurrent sessions.
        # 2. Execute `db.execute(select(InventoryItem).filter(...).with_for_update())`.
        # 3. Check requested quantity against (total_quantity - reserved_quantity).
        # 4. If all items available, update reserved_quantity and create StockAllocation.
        # 5. If any item fails, raise InsufficientInventoryError (triggering rollback).
        raise NotImplementedError(
            "Atomic inventory reservation must be implemented by the engineer."
        )

    def release_reservation(self, db: Session, order_reference: str) -> None:
        """
        Scaffolded reservation release.
        """
        # TODO [Engineer Implementation]:
        # Find all allocations with status=RESERVED for order_reference,
        # decrement reserved_quantity, and set status=RELEASED.
        raise NotImplementedError("Reservation release must be implemented by the engineer.")
