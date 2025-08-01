from datetime import datetime
from typing import Optional, List

from fastapi.params import Query
from pydantic import BaseModel, field_validator, Field, ConfigDict
import uuid

class StarSchema(BaseModel):
    name: str = Query(min_length=1, max_length=20)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.title()

class StarsDetailSchema(StarSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class GenresSchema(BaseModel):
    name: str = Query(min_length=1, max_length=20)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.title()

class GenresDetailSchema(GenresSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)

class GenresMoviesCountSchema(GenresDetailSchema):
    movies_count: int

    model_config = ConfigDict(from_attributes=True)


class DirectorSchema(BaseModel):
    name: str = Query(min_length=1, max_length=40)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.title()

class DirectorsDetailSchema(DirectorSchema):
    name: str

    model_config = ConfigDict(from_attributes=True)


class CommentSchema(BaseModel):
    id: int
    text: str
    user_profile_id: int

    model_config = ConfigDict(from_attributes=True)


class ReactionSchema(BaseModel):
    id: int
    reaction_type: str
    user_profile_id: int

    model_config = ConfigDict(from_attributes=True)


class MovieBaseSchema(BaseModel):
    uuid: uuid.UUID
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]
    description: Optional[str]
    price: float
    available: bool
    certification_id: int

    model_config = ConfigDict(from_attributes=True)

class MoviesOrderListSchema(MovieBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)

class MovieListSchema(MovieBaseSchema):
    id: int
    stars: List[StarsDetailSchema]
    genres: List[GenresDetailSchema]
    directors: List[DirectorsDetailSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(MovieBaseSchema):
    id: int
    uuid: uuid.UUID
    stars: List[StarsDetailSchema]
    genres: List[GenresDetailSchema]
    directors: List[DirectorsDetailSchema]

    class Config:
        from_attributes = True


class MovieCreateSchema(MovieBaseSchema):
    stars: List[str]
    genres: List[str]
    directors: List[str]

    @field_validator("stars", "genres", "directors", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: List[str]) -> List[str]:
        return [item.title() for item in value]


class MovieCreateResponseSchema(MovieBaseSchema):
    id: int
    uuid: uuid.UUID
    stars: List[StarsDetailSchema]
    genres: List[GenresDetailSchema]
    directors: List[DirectorsDetailSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieCommentBaseSchema(BaseModel):
    text: str
    user_profile_id: int
    movie_id: int


class MovieCommentCreateRequestSchema(BaseModel):
    text: str = Field(min_length=1, max_length=100)

    model_config = ConfigDict(from_attributes=True)


class MovieCommentCreateResponseSchema(MovieCommentBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)

class MovieCommentRepliesResponseSchema(MovieCommentBaseSchema):
    id: int
    parent_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "field_order": ["id", "parent_id", "text", "user_profile_id", "movie_id"]
        }
    )

class MovieUserReactionResponseSchema(BaseModel):
    message: str

    model_config = ConfigDict(from_attributes=True)


class MovieAddFavoriteResponseSchema(BaseModel):
    message: str


class MovieRatingRequestSchema(BaseModel):
    rating: int

    @field_validator("rating", mode="before")
    @classmethod
    def check_rating(cls, value: int) -> int:
        if value < 1 or value > 10:
            raise ValueError("Rating must be between 1 and 10.")
        return value

class MovieRatingResponseSchema(BaseModel):
    user_profile_id: int
    movie_id: int
    rating: int
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CommentLikeResponseSchema(BaseModel):
    id: int
    comment_id: int
    user_profile_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)