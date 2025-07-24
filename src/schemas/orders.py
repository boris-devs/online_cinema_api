import decimal
from datetime import datetime

from pydantic import BaseModel

from schemas import MoviesOrderListSchema


class OrderListSchema(BaseModel):
    time_order: datetime
    movies: list[MoviesOrderListSchema]
    total_amount: decimal.Decimal
    order_status: str
