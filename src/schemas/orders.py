import decimal

from pydantic import BaseModel


class OrderListSchema(BaseModel):
    count_movies: int
    total_amount: decimal.Decimal
