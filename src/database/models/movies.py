import enum
from datetime import datetime

from sqlalchemy.types import Uuid

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (Integer, String, ForeignKey, types, Float, Text, DECIMAL, Table, Column,
                        UniqueConstraint, Enum as SQLEnum, DateTime, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from database import Base

if TYPE_CHECKING:
    from database import UserProfileModel, CartItemsModel


class ReactionType(enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


MovieStarsModel = Table(
    "movies_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("star_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True),
)

MovieGenresModel = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

MovieDirectorsModel = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True),
)

MovieFavoritesModel = Table(
    "movie_favorites",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("user_profile_id", ForeignKey("user_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime(timezone=True), server_default=func.now())
)


class StarsModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieStarsModel,
        back_populates="stars")


class GenresModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieGenresModel,
        back_populates="genres")


class DirectorsModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieModel"]] = relationship(
        "MovieModel",
        secondary=MovieDirectorsModel,
        back_populates="directors")


class ReactionsModel(Base):
    __tablename__ = "reactions"
    __table_args__ = (UniqueConstraint('user_profile_id', 'movie_id', name='_user_profile_movie_uc'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reaction_type: Mapped[ReactionType] = mapped_column(SQLEnum(ReactionType))
    user_profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    user_profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="reactions")
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="reactions")


class CertificationsModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", back_populates="certification")


class RatingsModel(Base):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"))
    user_profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="ratings")
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="ratings")
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('user_profile_id', 'movie_id', name='_user_profile_movie_rating_uc'),)

    @validates("rating")
    def validate_rating(self, key, value):
        if value < 1 or value > 10:
            raise ValueError("Rating must be between 1 and 10.")
        return value


class NotificationsModel(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"))
    user_profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="notifications")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    comment: Mapped["CommentsModel"] = relationship("CommentsModel", back_populates="notification")
    movie_id: Mapped[Optional[int]] = mapped_column(ForeignKey("movies.id", ondelete="SET NULL"), nullable=True)
    movie_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommentsModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text(), nullable=False)
    user_profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))
    user_profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="comments")
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="comments")
    comment_likes: Mapped[list["CommentLikesModel"]] = relationship("CommentLikesModel", back_populates="comment")

    parent: Mapped[Optional["CommentsModel"]] = relationship("CommentsModel", remote_side=[id],
                                                             back_populates="replies")
    replies: Mapped[list["CommentsModel"]] = relationship("CommentsModel", back_populates="parent")
    notification: Mapped["NotificationsModel"] = relationship("NotificationsModel", back_populates="comment")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommentLikesModel(Base):
    __tablename__ = "comment_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"))
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_profile: Mapped["UserProfileModel"] = relationship("UserProfileModel", back_populates="comment_likes")
    comment: Mapped["CommentsModel"] = relationship("CommentsModel", back_populates="comment_likes")

    __table_args__ = (UniqueConstraint('user_profile_id', 'comment_id', name='_user_profile_comment_uc'),)


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid: Mapped[Uuid] = mapped_column(types.UUID(as_uuid=True), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False)
    certification: Mapped["CertificationsModel"] = relationship("CertificationsModel", back_populates="movies")
    ratings: Mapped[list["RatingsModel"]] = relationship("RatingsModel", back_populates="movie")

    in_favorites: Mapped[list["UserProfileModel"]] = relationship(
        "UserProfileModel",
        secondary="movie_favorites",
        back_populates="favorite_movies")

    stars: Mapped[list["StarsModel"]] = relationship(
        "StarsModel",
        secondary=MovieStarsModel,
        back_populates="movies")

    genres: Mapped[list["GenresModel"]] = relationship(
        "GenresModel",
        secondary=MovieGenresModel,
        back_populates="movies")

    directors: Mapped[list["DirectorsModel"]] = relationship(
        "DirectorsModel",
        secondary=MovieDirectorsModel,
        back_populates="movies")

    reactions: Mapped[list["ReactionsModel"]] = relationship("ReactionsModel", back_populates="movie")

    comments: Mapped[list["CommentsModel"]] = relationship("CommentsModel", back_populates="movie")

    in_carts: Mapped[list["CartItemsModel"]] = relationship("CartItemsModel",
                                                            back_populates="movie")
