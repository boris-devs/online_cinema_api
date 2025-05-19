from typing import Optional

from pydantic import BaseModel


class StarsSchema(BaseModel):
    id: int
    name: str


class GenresSchema(BaseModel):
    id: int
    name: str


class DirectorsSchema(BaseModel):
    id: int
    name: str


class MovieBaseSchema(BaseModel):
    id: int
    uuid: str
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]
    description: Optional[str]
    price: Optional[float]
    certification_id: int
    stars: list[StarsSchema]
    genres: list[GenresSchema]
    directors: list[DirectorsSchema]


class MovieListSchema(MovieBaseSchema):
    pass

class MovieDetailSchema(MovieBaseSchema):
    pass
