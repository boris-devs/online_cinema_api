from pydantic import BaseModel, ConfigDict


class CartAddMovieResponseSchema(BaseModel):
    cart_id: int
    movie_id: int

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CartMoviesResponseSchema(BaseModel):
    name: str
    price: float
    year: int
    genres: list[GenreSchema]

    model_config = ConfigDict(from_attributes=True)
