from typing import Optional, List

from pydantic import BaseModel, field_validator, Field
import uuid


class StarsSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class GenresSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class DirectorsSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CommentSchema(BaseModel):
    id: int
    text: str
    user_profile_id: int

    class Config:
        from_attributes = True


class ReactionSchema(BaseModel):
    id: int
    reaction_type: str
    user_profile_id: int

    class Config:
        from_attributes = True


class MovieBaseSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]
    description: Optional[str]
    price: float
    certification_id: int

    class Config:
        from_attributes = True


class MovieListSchema(MovieBaseSchema):
    id: int
    stars: List[StarsSchema]
    genres: List[GenresSchema]
    directors: List[DirectorsSchema]

    class Config:
        from_attributes = True


class MovieDetailSchema(MovieBaseSchema):
    id: int
    uuid: uuid.UUID
    stars: List[StarsSchema]
    genres: List[GenresSchema]
    directors: List[DirectorsSchema]

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
    stars: List[StarsSchema]
    genres: List[GenresSchema]
    directors: List[DirectorsSchema]

    class Config:
        from_attributes = True


class MovieCommentBaseSchema(BaseModel):
    text: str
    user_profile_id: int
    movie_id: int


class MovieCommentCreateRequestSchema(BaseModel):
    text: str = Field(min_length=1, max_length=100)

    class Config:
        from_attributes = True


class MovieCommentCreateResponseSchema(MovieCommentBaseSchema):
    id: int

    class Config:
        from_attributes = True


class MovieUserReactionResponseModel(BaseModel):
    message: str

    class Config:
        from_attributes = True


class MovieAddFavoriteResponseSchema(BaseModel):
    message: str
