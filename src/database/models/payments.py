import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum, Float, DECIMAL, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from database import UserModel, OrderItemsModel


class PaymentStatusEnum(str, enum.Enum):
    successful: str = 'Successful'
    canceled: str = 'Canceled'
    refunded: str = 'Refunded'


class PaymentsModel(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    user_id: Mapped[int] = ForeignKey('users.id', ondelete='CASCADE')
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="payments")
    order_id: Mapped[int] = ForeignKey('orders.id', ondelete='CASCADE')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    status: Mapped[PaymentStatusEnum] = mapped_column(Enum(PaymentStatusEnum), nullable=False,
                                                      default=PaymentStatusEnum.successful)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    external_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    items: Mapped["PaymentsItemsModel"] = relationship("PaymentsItemsModel", back_populates="payment")

class PaymentsItemsModel(Base):
    __tablename__ = 'payments_items'
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    payment_id: Mapped["PaymentsModel"] = ForeignKey('payments.id', ondelete='CASCADE')
    payment: Mapped["PaymentsModel"] = relationship("PaymentsModel", back_populates="items")
    order_item_id: Mapped["OrderItemsModel"] = ForeignKey('order_items.id', ondelete='CASCADE')
    price_at_payment: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)