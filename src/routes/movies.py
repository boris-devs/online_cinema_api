import uuid
from enum import Enum
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import add_pagination, Page
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import selectinload, joinedload
from starlette import status

from database.models.accounts import UserProfileModel
from database.models.movies import MovieModel, StarsModel, GenresModel, DirectorsModel, CommentsModel, ReactionsModel, \
    ReactionType
from schemas import MovieListSchema
from database import get_db
from schemas.movies import MovieDetailSchema, MovieCreateSchema, MovieCommentCreateResponseSchema, \
    MovieCommentCreateRequestSchema, MovieUserReactionResponseModel, MovieCreateResponseSchema
from security.auth import get_current_user

router = APIRouter()


class MovieSortField(str, Enum):
    YEAR_ASC = "year_asc"
    YEAR_DESC = "year_desc"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    IMDB_ASC = "imdb_asc"
    IMDB_DESC = "imdb_desc"
    POPULARITY_ASC = "popularity_asc"
    POPULARITY_DESC = "popularity_desc"


@router.get("/movies/", response_model=Page[MovieListSchema])
async def get_movies(
        db: AsyncSession = Depends(get_db),
        year: Optional[int] = Query(None, description="Filter by exact release year"),
        year_min: Optional[int] = Query(None, description="Minimum release year"),
        year_max: Optional[int] = Query(None, description="Maximum release year"),
        imdb_min: Optional[float] = Query(None, ge=0, le=10, description="Minimum IMDb rating (0-10)"),
        imdb_max: Optional[float] = Query(None, ge=0, le=10, description="Maximum IMDb rating (0-10)"),
        price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
        price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
        genres: Optional[List[str]] = Query(None, description="Filter by genre names"),
        directors: Optional[List[str]] = Query(None, description="Filter by director names"),
        actors: Optional[List[str]] = Query(None, description="Filter by actor names"),
        search: Optional[str] = Query(None, description="Search in title, description, actors or directors"),
        sort_by: Optional[MovieSortField] = Query(
            MovieSortField.YEAR_DESC,
            description="Sort by field and direction"
        ),
):
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.directors),
        joinedload(MovieModel.stars)
    )

    if year:
        query = query.where(MovieModel.year == year)

    if year_min:
        query = query.where(MovieModel.year >= year_min)

    if year_max:
        query = query.where(MovieModel.year <= year_max)

    if imdb_min:
        query = query.where(MovieModel.imdb >= imdb_min)

    if imdb_max:
        query = query.where(MovieModel.imdb <= imdb_max)

    if price_min:
        query = query.where(MovieModel.price >= price_min)

    if price_max:
        query = query.where(MovieModel.price <= price_max)

    if genres:
        query = query.where(GenresModel.name.in_(genres))

    if directors:
        query = query.where(DirectorsModel.name.in_(directors))

    if actors:
        query = query.where(StarsModel.name.in_(actors))

    if search:
        search = f"%{search}%"
        query = query.where(
            or_(
                MovieModel.name.ilike(search),
                MovieModel.description.ilike(search),
                DirectorsModel.name.ilike(search),
                StarsModel.name.ilike(search)
            )
        )

    if sort_by == MovieSortField.YEAR_ASC:
        query = query.order_by(MovieModel.year.asc())
    elif sort_by == MovieSortField.YEAR_DESC:
        query = query.order_by(MovieModel.year.desc())
    elif sort_by == MovieSortField.PRICE_ASC:
        query = query.order_by(MovieModel.price.asc())
    elif sort_by == MovieSortField.PRICE_DESC:
        query = query.order_by(MovieModel.price.desc())
    elif sort_by == MovieSortField.IMDB_ASC:
        query = query.order_by(MovieModel.imdb.asc())
    elif sort_by == MovieSortField.IMDB_DESC:
        query = query.order_by(MovieModel.imdb.desc())
    elif sort_by == MovieSortField.POPULARITY_ASC:
        query = query.order_by(MovieModel.votes.asc())
    elif sort_by == MovieSortField.POPULARITY_DESC:
        query = query.order_by(MovieModel.votes.desc())

    return await paginate(db, query)


@router.get("/movies/detail/{id_film}/", response_model=MovieDetailSchema)
async def get_movie_detail(id_film: int, db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(MovieModel)
                            .where(MovieModel.id == id_film)
                            .options(selectinload(MovieModel.genres),
                                     selectinload(MovieModel.stars),
                                     selectinload(MovieModel.directors),
                                     selectinload(MovieModel.certification),
                                     selectinload(MovieModel.reactions),
                                     selectinload(MovieModel.comments)))
    result = stmt.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail="Movie not found.")

    return MovieDetailSchema.model_validate(result)


@router.post("/movies/add/", response_model=MovieCreateResponseSchema, status_code=status.HTTP_201_CREATED)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(MovieModel).where(MovieModel.name == movie.name))
    result = stmt.scalars().first()
    if result:
        raise HTTPException(status_code=400, detail="Movie already exists.")

    try:
        stars = []
        for star_name in movie.stars:
            stmt = await db.execute(select(StarsModel).where(StarsModel.name == star_name))
            star = stmt.scalars().first()
            if not star:
                star = StarsModel(name=star_name)
                db.add(star)
                await db.flush()
            stars.append(star)

        genres = []
        for genre_name in movie.genres:
            stmt = await db.execute(select(GenresModel).where(GenresModel.name == genre_name))
            genre = stmt.scalars().first()
            if not genre:
                genre = GenresModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        directors = []
        for director_name in movie.directors:
            stmt = await db.execute(select(DirectorsModel).where(DirectorsModel.name == director_name))
            director = stmt.scalars().first()
            if not director:
                director = DirectorsModel(name=director_name)
                db.add(director)
                await db.flush()
            directors.append(director)

        movie_db = MovieModel(
            uuid=uuid.uuid4(),
            name=movie.name,
            year=movie.year,
            time=movie.time,
            imdb=movie.imdb,
            votes=movie.votes,
            meta_score=movie.meta_score,
            gross=movie.gross,
            description=movie.description,
            price=movie.price,
            certification_id=movie.certification_id,
            stars=stars,
            genres=genres,
            directors=directors,
        )
        db.add(movie_db)
        await db.commit()
        await db.refresh(movie_db, ["stars", "genres", "directors"])

        return MovieCreateResponseSchema.model_validate(movie_db)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.post("/movies/detail/{id_film}/comment/", response_model=MovieCommentCreateResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def create_comment(
        id_film: int,
        comment: MovieCommentCreateRequestSchema,
        db: AsyncSession = Depends(get_db),
        current_user_id: int = Depends(get_current_user)
):
    stmt_user_profile = await db.execute(select(UserProfileModel).where(UserProfileModel.user_id == current_user_id))
    existing_user_profile = stmt_user_profile.scalars().first()
    if not existing_user_profile:
        raise HTTPException(status_code=404, detail="User not found.")

    stmt_movie = await db.execute(select(MovieModel).where(MovieModel.id == id_film))
    existing_movie = stmt_movie.scalars().first()
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    comment = CommentsModel(
        text=comment.text,
        user_profile_id=existing_user_profile.id,
        movie_id=existing_movie.id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return MovieCommentCreateResponseSchema.model_validate(comment)


@router.delete("/movies/{id_film}/{id_comment}/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
        id_film: int,
        id_comment: int,
        db: AsyncSession = Depends(get_db),
        current_user_id: int = Depends(get_current_user)
):
    stmt_user_profile = await db.execute(select(UserProfileModel).where(UserProfileModel.user_id == current_user_id))
    existing_user_profile = stmt_user_profile.scalars().first()
    if not existing_user_profile:
        raise HTTPException(status_code=404, detail="User not found.")

    stmt_movie = await db.execute(select(MovieModel).where(MovieModel.id == id_film))
    existing_movie = stmt_movie.scalars().first()
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_comment = await db.execute(select(CommentsModel).where(CommentsModel.id == id_comment,
                                                                CommentsModel.user_profile_id == existing_user_profile.id))
    existing_comment = stmt_comment.scalars().first()
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    await db.delete(existing_comment)
    await db.commit()
    return


@router.post("/movies/{id_film}/like/",
             response_model=MovieUserReactionResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def like_movie(
        id_film: int,
        current_user_id: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(MovieModel).where(MovieModel.id == id_film))
    existing_movie = stmt.scalars().first()
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_user_profile = await db.execute(select(UserProfileModel).where(UserProfileModel.user_id == current_user_id))
    existing_user_profile = stmt_user_profile.scalars().first()
    if not existing_user_profile:
        raise HTTPException(status_code=404, detail="User not found.")

    stmt_reaction = await db.execute(select(ReactionsModel)
                                     .where(ReactionsModel.user_profile_id == existing_user_profile.id,
                                            ReactionsModel.movie_id == existing_movie.id))
    existing_reaction = stmt_reaction.scalars().first()

    if existing_reaction:
        if existing_reaction.reaction_type == ReactionType.LIKE:
            raise HTTPException(status_code=400, detail="You have already liked this movie.")

        elif existing_reaction.reaction_type == ReactionType.DISLIKE:
            existing_reaction.reaction_type = ReactionType.LIKE
            await db.commit()
            await db.refresh(existing_reaction)
            return MovieUserReactionResponseModel(message="Movie liked successfully")


    else:
        like = ReactionsModel(
            user_profile_id=existing_user_profile.id,
            movie_id=existing_movie.id,
            reaction_type=ReactionType.LIKE
        )
        db.add(like)
        await db.commit()
        await db.refresh(like)

        return MovieUserReactionResponseSchema(message="Movie liked successfully")


@router.post("/movies/{id_film}/dislike/",
             response_model=MovieUserReactionResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def dislike_movie(id_film: int,
                        current_user_id: int = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(MovieModel).where(MovieModel.id == id_film))
    existing_movie = stmt.scalars().first()
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_user_profile = await db.execute(select(UserProfileModel).where(UserProfileModel.user_id == current_user_id))
    existing_user_profile = stmt_user_profile.scalars().first()
    if not existing_user_profile:
        raise HTTPException(status_code=404, detail="User not found.")

    stmt_reaction = await db.execute(select(ReactionsModel)
                                     .where(ReactionsModel.user_profile_id == existing_user_profile.id,
                                            ReactionsModel.movie_id == existing_movie.id))
    existing_reaction = stmt_reaction.scalars().first()

    if existing_reaction:
        if existing_reaction.reaction_type == ReactionType.DISLIKE:
            raise HTTPException(status_code=400, detail="You have already disliked this movie.")

        elif existing_reaction.reaction_type == ReactionType.LIKE:
            existing_reaction.reaction_type = ReactionType.DISLIKE
            await db.commit()
            await db.refresh(existing_reaction)
            return MovieUserReactionResponseSchema(message="Movie disliked successfully")

    else:
        dislike = ReactionsModel(
            user_profile_id=existing_user_profile.id,
            movie_id=existing_movie.id,
            reaction_type=ReactionType.DISLIKE
        )
        db.add(dislike)
        await db.commit()
        await db.refresh(dislike)

        return MovieUserReactionResponseSchema(message="Movie disliked successfully")


@router.delete("/movies/{id_film}/delete_reaction/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(id_film: int,
                          current_user_id: int = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(MovieModel).where(MovieModel.id == id_film))
    existing_movie = stmt.scalars().first()
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_user_profile = await db.execute(select(UserProfileModel).where(UserProfileModel.user_id == current_user_id))
    existing_user_profile = stmt_user_profile.scalars().first()
    if not existing_user_profile:
        raise HTTPException(status_code=404, detail="User not found.")

    stmt_reaction = await db.execute(select(ReactionsModel)
                                     .where(ReactionsModel.user_profile_id == existing_user_profile.id,
                                            ReactionsModel.movie_id == existing_movie.id))
    existing_reaction = stmt_reaction.scalars().first()
    if not existing_reaction:
        raise HTTPException(status_code=404, detail="Reaction not found.")

    await db.delete(existing_reaction)
    await db.commit()
    return


add_pagination(router)
