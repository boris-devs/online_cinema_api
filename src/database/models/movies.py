from sqlalchemy.types import Uuid

from typing import Optional, List

from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint, types, Float, Text, DECIMAL, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class StarsModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieStarsModel"]] = relationship(
        "MovieModel",
        secondary="MovieStarsModel",
        back_populates="star")


class GenresModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieGenresModel"]] = relationship(
        "MovieModel",
        secondary="MovieGenresModel",
        back_populates="genre")


class DirectorsModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieDirectorsModel"]] = relationship("MovieModel", secondary="MovieDirectorsModel",
                                                               back_populates="director")


MovieStarsModel = Table(
    "movies_languages",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("language_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True),
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


class CertificationsModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    movies: Mapped[list["MovieModel"]] = relationship("MovieModel", back_populates="certification")


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

    stars: Mapped[list["StarsModel"]] = relationship(
        "StarsModel",
        secondary=MovieStarsModel,
        back_populates="movies")

    genres: Mapped[list["MovieGenresModel"]] = relationship(
        "GenresModel",
        secondary=MovieGenresModel,
        back_populates="movie")

    directors: Mapped[list["MovieDirectorsModel"]] = relationship(
        "DirectorsModel",
        secondary=MovieDirectorsModel,
        back_populates="movie")
