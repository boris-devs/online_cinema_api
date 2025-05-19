from sqlalchemy.types import Uuid

from typing import Optional, List

from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint, types, Float, Text, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class StarsModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieStarsModel"]] = relationship(back_populates="star")

class GenresModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieGenresModel"]] = relationship(back_populates="genre")

class DirectorsModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    movies: Mapped[List["MovieDirectorsModel"]] = relationship(back_populates="director")



class MovieStarsModel(Base):
    __tablename__ = "movie_stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="stars")
    star_id: Mapped[int] = mapped_column(ForeignKey("stars.id", ondelete="CASCADE"), nullable=False)
    star: Mapped["StarsModel"] = relationship("StarModel", back_populates="movies")

    __table_args__ = (
        UniqueConstraint("movie_id", "star_id"),
    )


class MovieGenresModel(Base):
    __tablename__ = "movie_genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="genres")
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), nullable=False)
    genre: Mapped["GenresModel"] = relationship("GenresModel", back_populates="movies")

    __table_args__ = (
        UniqueConstraint("movie_id", "genre_id"),
    )


class MovieDirectorsModel(Base):
    __tablename__ = "movie_directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="directors")
    director_id: Mapped[int] = mapped_column(ForeignKey("directors.id", ondelete="CASCADE"), nullable=False)
    director: Mapped["DirectorsModel"] = relationship("DirectorsModel", back_populates="movies")

    __table_args__ = (
        UniqueConstraint("movie_id", "director_id"),
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
    stars: Mapped[List["MovieStarsModel"]] = relationship(back_populates="movie")
    genres: Mapped[List["MovieGenresModel"]] = relationship(back_populates="movie")
    directors: Mapped[List["MovieDirectorsModel"]] = relationship(back_populates="movie")