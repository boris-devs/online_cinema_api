from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from database import MovieModel

class CartsModel(Base):
    __tablename__ = 'carts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="RESTRICT"), nullable=False)
    items: Mapped[list["CartItemsModel"]] = relationship("CartItemsModel", back_populates="cart")


class CartItemsModel(Base):
    __tablename__ = 'cart_items'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey('carts.id', ondelete="CASCADE"), nullable=False)
    cart: Mapped["CartsModel"] = relationship("CartsModel", back_populates="items")
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    movie_id: Mapped[int] = mapped_column(ForeignKey('movies.id', ondelete="CASCADE"), nullable=False)
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="in_carts")

    __table_args__ = (UniqueConstraint('cart_id', 'movie_id', name='cart_items_uc'),)