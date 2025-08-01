import decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas import MoviesOrderListSchema


class OrderItemsSchema(BaseModel):
    id: int
    movie_id: int
    movie: MoviesOrderListSchema

    model_config = ConfigDict(from_attributes=True)


class OrderBaseSchema(BaseModel):
    created_at: datetime
    total_amount: decimal.Decimal
    status: str

class OrdersUserListSchema(OrderBaseSchema):
    user_id: int
    id: int

    model_config = ConfigDict(from_attributes=True)

class OrderCreateSchema(OrderBaseSchema):
    movies: list[MoviesOrderListSchema]

    model_config = ConfigDict(from_attributes=True)

class OrdersUsersModeratorResponseSchema(OrderBaseSchema):
    id: int
    user_id: int
    items: list[OrderItemsSchema]

    model_config = ConfigDict(from_attributes=True)
