import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AllocationStatus(enum.StrEnum):
    RESERVED = "RESERVED"
    COMMITTED = "COMMITTED"
    RELEASED = "RELEASED"


class InventoryItem(Base):
    """
    SQLAlchemy 2.0 model representing a warehouse inventory item.
    """

    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    total_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Optimistic locking support / concurrency audit tracking
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    allocations: Mapped[list["StockAllocation"]] = relationship(
        "StockAllocation", back_populates="inventory_item"
    )

    @property
    def available_quantity(self) -> int:
        """Calculates instantly sellable stock."""
        return self.total_quantity - self.reserved_quantity


class StockAllocation(Base):
    """
    Record of inventory reserved for an order within a specific warehouse.
    """

    __tablename__ = "stock_allocations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inventory_item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False
    )
    order_reference: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    allocated_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AllocationStatus] = mapped_column(
        Enum(AllocationStatus), default=AllocationStatus.RESERVED, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inventory_item: Mapped["InventoryItem"] = relationship(
        "InventoryItem", back_populates="allocations"
    )
