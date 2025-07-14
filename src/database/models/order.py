import decimal
import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from database import UserModel


class StatusOrderEnum(str, enum.Enum):
    pending: str = "pending"
    paid: str = "paid"
    cancelled: str = "cancelled"


class OrdersModel(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="RESTRICT"), nullable=False)
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    status: Mapped[StatusOrderEnum] = mapped_column(Enum(StatusOrderEnum), nullable=False,
                                                    default=StatusOrderEnum.pending)
    total_amount: Mapped[decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

class OrderItemsModel(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id', ondelete="CASCADE"), nullable=False)
    price_at_order: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)