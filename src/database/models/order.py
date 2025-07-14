import decimal
import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from database import UserModel, MovieModel


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
    items: Mapped[list["OrderItemsModel"]] = relationship("OrderItemsModel", back_populates="order")

    def __repr__(self):
        return f"OrdersModel(id={self.id}, user_id={self.user_id}, status={self.status}, created_at={self.created_at})"

class OrderItemsModel(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete="CASCADE"), nullable=False)
    order: Mapped["OrdersModel"] = relationship("OrdersModel", back_populates="items")
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id', ondelete="CASCADE"), nullable=False)
    movie: Mapped["MovieModel"] = relationship("MovieModel")
    price_at_order: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    def __repr__(self):
        return f"OrderItemsModel(id={self.id}, order_id={self.order_id}, movie_id={self.movie_id}, price={self.price_at_order})"