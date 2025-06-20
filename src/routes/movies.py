import uuid
from enum import Enum
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import add_pagination, Page
from sqlalchemy import select, or_, insert, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import selectinload, joinedload
from starlette import status

from database.models.accounts import UserProfileModel, UserModel
from database.models.movies import MovieModel, StarsModel, GenresModel, DirectorsModel, CommentsModel, ReactionsModel, \
    ReactionType, MovieFavoritesModel, RatingsModel, MovieGenresModel, CommentLikesModel, NotificationsModel, \
    MovieStarsModel, MovieDirectorsModel
from schemas import MovieListSchema
from database import get_db
from schemas.movies import (MovieDetailSchema, MovieCreateSchema, MovieCommentCreateResponseSchema,
                            MovieCommentCreateRequestSchema, MovieUserReactionResponseSchema, MovieCreateResponseSchema,
                            MovieAddFavoriteResponseSchema, MovieRatingRequestSchema, MovieRatingResponseSchema,
                            GenresMoviesCountSchema, CommentLikeResponseSchema, MovieCommentRepliesResponseSchema,
                            GenresDetailSchema, GenresSchema, StarSchema, StarsDetailSchema, DirectorsDetailSchema,
                            DirectorSchema)
from security.auth import get_current_user


async def current_user_profile(
        current_user_id: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user_profile = await db.execute(select(UserProfileModel).where(UserProfileModel.user_id == current_user_id))
    existing_user_profile = user_profile.scalar_one_or_none()
    if not existing_user_profile:
        raise HTTPException(status_code=404, detail="User not found.")
    return existing_user_profile


async def current_moderator_profile(
        current_user_id: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user_profile = await db.execute(select(UserProfileModel)
    .join(UserModel)
    .where(
        UserProfileModel.user_id == current_user_id,
        or_(UserModel.group_id == 2,
            UserModel.group_id == 3)))
    existing_user_profile = user_profile.scalar_one_or_none()
    if not existing_user_profile:
        raise HTTPException(status_code=404, detail="User not found.")
    return existing_user_profile


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


@router.get("/movies/detail/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(MovieModel)
                            .where(MovieModel.id == movie_id)
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
async def add_movie(movie: MovieCreateSchema,
                    _moderator_profile: UserProfileModel = Depends(current_moderator_profile),
                    db: AsyncSession = Depends(get_db)):
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


@router.post("/genres/add/", response_model=GenresDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_genre(
        genre: GenresSchema,
        _moderator_profile: UserProfileModel = Depends(current_moderator_profile),
        db: AsyncSession = Depends(get_db)
):
    existing_genre = await db.execute(select(GenresModel).where(GenresModel.name == genre.name))
    existing_genre = existing_genre.scalar_one_or_none()
    if existing_genre:
        raise HTTPException(status_code=400, detail="Genre already exists.")
    new_genre = GenresModel(name=genre.name)
    db.add(new_genre)
    await db.commit()
    return GenresDetailSchema.model_validate(new_genre)


@router.delete("/genres/{genre_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genre(
        genre_id: int,
        _moderator_profile: UserProfileModel = Depends(current_moderator_profile),
        db: AsyncSession = Depends(get_db)
):
    genre = await db.get(GenresModel, genre_id)
    if not genre:
        raise HTTPException(status_code=400, detail="Genre not found.")
    current_genre_in_movies = await db.execute(select(MovieGenresModel).where(MovieGenresModel.c.genre_id == genre_id))
    current_genre_in_movies = current_genre_in_movies.scalars().first()
    if current_genre_in_movies:
        raise HTTPException(status_code=400, detail="The current genre corresponds to one or more movies")

    await db.delete(genre)
    await db.commit()
    return


@router.post("/stars/create/", response_model=StarsDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_star(
        star: StarSchema,
        _moderator_profile: UserProfileModel = Depends(current_moderator_profile),
        db: AsyncSession = Depends(get_db)
):
    existing_star = await db.execute(select(StarsModel).where(StarsModel.name == star.name))
    existing_star = existing_star.scalar_one_or_none()
    if existing_star:
        raise HTTPException(status_code=400, detail="Star already exists.")
    star = StarsModel(name=star.name)
    db.add(star)
    await db.commit()
    return StarsDetailSchema.model_validate(star)


@router.delete("/stars/{star_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_star(
        star_id: int,
        _moderator_profile: UserProfileModel = Depends(current_moderator_profile),
        db: AsyncSession = Depends(get_db)
):
    star = await db.get(StarsModel, star_id)
    if not star:
        raise HTTPException(status_code=400, detail="Star not found.")
    current_star_in_movies = await db.execute(select(MovieStarsModel).where(MovieStarsModel.c.star_id == star_id))
    current_star_in_movies = current_star_in_movies.scalars().first()
    if current_star_in_movies:
        raise HTTPException(status_code=400, detail="The current star corresponds to one or more movies")

    await db.delete(star)
    await db.commit()
    return


@router.post("/directors/create/", response_model=DirectorsDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_director(
        director: DirectorSchema,
        _moderator_profile: UserProfileModel = Depends(current_moderator_profile),
        db: AsyncSession = Depends(get_db)
):
    existing_director = await db.execute(select(DirectorsModel).where(DirectorsModel.name == director.name))
    existing_director = existing_director.scalar_one_or_none()
    if existing_director:
        raise HTTPException(status_code=400, detail="Director already exists.")
    director = DirectorsModel(name=director.name)
    db.add(director)
    await db.commit()
    return DirectorsDetailSchema.model_validate(director)


@router.delete("/directors/{director_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_director(
        director_id: int,
        _moderator_profile: UserProfileModel = Depends(current_moderator_profile),
        db: AsyncSession = Depends(get_db)
):
    director = await db.get(DirectorsModel, director_id)
    if not director:
        raise HTTPException(status_code=400, detail="Director not found.")

    current_director_in_movie = await db.execute(
        select(MovieDirectorsModel).where(MovieDirectorsModel.c.director_id == director_id))
    current_director_in_movie = current_director_in_movie.scalars().first()
    if current_director_in_movie:
        raise HTTPException(status_code=400, detail="The current star corresponds to one or more movies")
    await db.delete(director)
    await db.commit()
    return


@router.post("/movies/{movie_id}/comment/", response_model=MovieCommentCreateResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def create_comment(
        movie_id: int,
        comment: MovieCommentCreateRequestSchema,
        db: AsyncSession = Depends(get_db),
        user_profile: UserProfileModel = Depends(current_user_profile)
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    comment = CommentsModel(
        text=comment.text,
        user_profile_id=user_profile.id,
        movie_id=movie.id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return MovieCommentCreateResponseSchema.model_validate(comment)


@router.delete("/movies/{movie_id}/{comment_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
        movie_id: int,
        comment_id: int,
        db: AsyncSession = Depends(get_db),
        user_profile: UserProfileModel = Depends(current_user_profile)
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_comment = await db.execute(select(CommentsModel).where(CommentsModel.id == comment_id,
                                                                CommentsModel.user_profile_id == user_profile.id))
    existing_comment = stmt_comment.scalars().first()
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    await db.delete(existing_comment)
    await db.commit()
    return


@router.post("/comments/{parent_comment_id}/replies/",
             response_model=MovieCommentRepliesResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def create_replies(
        parent_comment_id: int,
        comment_data: MovieCommentCreateRequestSchema,
        user_profile: UserProfileModel = Depends(current_user_profile),
        db: AsyncSession = Depends(get_db)
):
    parent_comment = await db.get(CommentsModel, parent_comment_id)
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    reply_comment = CommentsModel(
        text=comment_data.text,
        user_profile_id=user_profile.id,
        movie_id=parent_comment.movie_id,
        parent_id=parent_comment_id
    )
    db.add(reply_comment)

    if user_profile.id != parent_comment.user_profile_id:
        notification = NotificationsModel(
            user_profile_id=user_profile.id,
            message=f"User {user_profile.first_name} {user_profile.last_name} answer on your comment.",
            comment_id=parent_comment_id,
        )
        db.add(notification)

    await db.commit()
    await db.refresh(reply_comment)

    return MovieCommentRepliesResponseSchema.model_validate(reply_comment)


@router.post("/comments/{comment_id}/like/", response_model=CommentLikeResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def like_comment(
        comment_id: int,
        user_profile: UserProfileModel = Depends(current_user_profile),
        db: AsyncSession = Depends(get_db)):
    existing_comment = await db.get(CommentsModel, comment_id)
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    existing_like_comment = await db.execute(
        select(CommentLikesModel)
        .where(CommentLikesModel.comment_id == comment_id,
               CommentLikesModel.user_profile_id == user_profile.id))
    existing_like_comment = existing_like_comment.scalar_one_or_none()
    if existing_like_comment:
        raise HTTPException(status_code=409, detail="You have already liked this comment.")

    record_like = CommentLikesModel(
        comment_id=comment_id,
        user_profile_id=user_profile.id
    )
    db.add(record_like)

    if user_profile.id != existing_comment.user_profile_id:
        notification = NotificationsModel(
            user_profile_id=user_profile.id,
            message=f"User {user_profile.first_name} {user_profile.last_name} liked your comment.",
            comment_id=comment_id)
        db.add(notification)
    await db.commit()
    await db.refresh(record_like)

    return CommentLikeResponseSchema.model_validate(record_like)


@router.delete("/comments/{comment_id}/delete_like/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_like_on_comment(comment_id: int,
                                 user_profile: UserProfileModel = Depends(current_user_profile),
                                 db: AsyncSession = Depends(get_db)):
    existing_comment = await db.execute(
        select(CommentLikesModel)
        .where(CommentLikesModel.comment_id == comment_id,
               CommentLikesModel.user_profile_id == user_profile.id))
    existing_comment = existing_comment.scalar_one_or_none()
    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    await db.delete(existing_comment)
    await db.commit()
    return


@router.post("/movies/{movie_id}/like/",
             response_model=MovieUserReactionResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def like_movie(
        movie_id: int,
        user_profile: UserProfileModel = Depends(current_user_profile),
        db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_reaction = await db.execute(select(ReactionsModel)
                                     .where(ReactionsModel.user_profile_id == user_profile.id,
                                            ReactionsModel.movie_id == movie.id))
    existing_reaction = stmt_reaction.scalars().first()

    if existing_reaction:
        if existing_reaction.reaction_type == ReactionType.LIKE:
            raise HTTPException(status_code=400, detail="You have already liked this movie.")

        elif existing_reaction.reaction_type == ReactionType.DISLIKE:
            existing_reaction.reaction_type = ReactionType.LIKE
            await db.commit()
            await db.refresh(existing_reaction)
            return MovieUserReactionResponseSchema(message="Movie liked successfully")


    else:
        like = ReactionsModel(
            user_profile_id=user_profile.id,
            movie_id=movie.id,
            reaction_type=ReactionType.LIKE
        )
        db.add(like)
        await db.commit()
        await db.refresh(like)

        return MovieUserReactionResponseSchema(message="Movie liked successfully")


@router.post("/movies/{movie_id}/dislike/",
             response_model=MovieUserReactionResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def dislike_movie(movie_id: int,
                        user_profile: UserProfileModel = Depends(current_user_profile),
                        db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_reaction = await db.execute(select(ReactionsModel)
                                     .where(ReactionsModel.user_profile_id == user_profile.id,
                                            ReactionsModel.movie_id == movie.id))
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
            user_profile_id=user_profile.id,
            movie_id=movie.id,
            reaction_type=ReactionType.DISLIKE
        )
        db.add(dislike)
        await db.commit()
        await db.refresh(dislike)

        return MovieUserReactionResponseSchema(message="Movie disliked successfully")


@router.delete("/movies/{movie_id}/delete_reaction/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(movie_id: int,
                          user_profile: UserProfileModel = Depends(current_user_profile),
                          db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_reaction = await db.execute(select(ReactionsModel)
                                     .where(ReactionsModel.user_profile_id == user_profile.id,
                                            ReactionsModel.movie_id == movie.id))
    existing_reaction = stmt_reaction.scalars().first()
    if not existing_reaction:
        raise HTTPException(status_code=404, detail="Reaction not found.")

    await db.delete(existing_reaction)
    await db.commit()
    return


@router.post("/movies/{movie_id}/add_to_favorite/",
             response_model=MovieAddFavoriteResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def add_to_favorite(
        movie_id: int,
        user_profile: UserProfileModel = Depends(current_user_profile),
        db: AsyncSession = Depends(get_db)
):
    stmt_existing_record = await db.execute(
        select(MovieFavoritesModel)
        .where(
            MovieFavoritesModel.c.movie_id == movie_id,
            MovieFavoritesModel.c.user_profile_id == user_profile.id
        ))
    existing_record = stmt_existing_record.scalars().all()
    if existing_record:
        raise HTTPException(status_code=400, detail="Movie already in favorite movies.")

    await db.execute(
        insert(MovieFavoritesModel)
        .values(movie_id=movie_id,
                user_profile_id=user_profile.id)
    )
    await db.commit()

    return "Successfully added to favorite movies."


@router.delete("/movies/{movie_id}/delete_favorite/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_from_favorite(
        movie_id: int,
        user_profile: UserProfileModel = Depends(current_user_profile),
        db: AsyncSession = Depends(get_db)
):
    stmt_existing_record = await db.execute(
        select(MovieFavoritesModel)
        .where(
            MovieFavoritesModel.c.movie_id == movie_id,
            MovieFavoritesModel.c.user_profile_id == user_profile.id
        ))
    existing_record = stmt_existing_record.scalars().all()
    if not existing_record:
        raise HTTPException(status_code=400, detail="Movie not in your favorite movies.")

    await db.execute(
        delete(MovieFavoritesModel)
        .where(
            MovieFavoritesModel.c.movie_id == movie_id,
            MovieFavoritesModel.c.user_profile_id == user_profile.id
        )
    )
    await db.commit()
    return


@router.get("/movies/favourites/", response_model=Page[MovieListSchema])
async def get_favourite_movies(
        db: AsyncSession = Depends(get_db),
        user_profile: UserProfileModel = Depends(current_user_profile),
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
    query = (select(MovieModel).join(
        MovieFavoritesModel,
        MovieFavoritesModel.c.movie_id == MovieModel.id
    ).where(
        MovieFavoritesModel.c.user_profile_id == user_profile.id
    )
    .options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.directors),
        joinedload(MovieModel.stars)
    ))

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


@router.get("/genres/", response_model=List[GenresMoviesCountSchema], status_code=status.HTTP_200_OK)
async def get_genres(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            GenresModel.id,
            GenresModel.name,
            func.count(MovieGenresModel.c.movie_id).label('movies_count')
        )
        .select_from(GenresModel)
        .join(
            MovieGenresModel,
            GenresModel.id == MovieGenresModel.c.genre_id,
            isouter=True
        )
        .group_by(GenresModel.id, GenresModel.name)
        .order_by(GenresModel.name)
    )

    result = await db.execute(query)
    genres = result.all()
    return genres


@router.get("/movies/{name_genre}/", response_model=Page[MovieListSchema])
async def get_movies_by_genre(
        name_genre: str,
        db: AsyncSession = Depends(get_db)):
    movies = select(MovieModel).options(joinedload(MovieModel.genres),
                                        joinedload(MovieModel.directors),
                                        joinedload(MovieModel.stars),
                                        joinedload(MovieModel.reactions),
                                        joinedload(MovieModel.comments)).where(
        MovieModel.genres.any(GenresModel.name == name_genre))

    return await paginate(db, movies)


@router.post("/movies/{movie_id}/rating/",
             response_model=MovieRatingResponseSchema,
             status_code=status.HTTP_201_CREATED)
async def add_rating(
        movie_id: int,
        data: MovieRatingRequestSchema,
        user_profile: UserProfileModel = Depends(current_user_profile),
        db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_rating = await db.execute(select(RatingsModel).where(RatingsModel.user_profile_id == user_profile.id,
                                                              RatingsModel.movie_id == movie.id))
    existing_rating = stmt_rating.scalar_one_or_none()
    if existing_rating:
        existing_rating.rating = data.rating
        await db.commit()
        await db.refresh(existing_rating)

        return existing_rating

    rating = RatingsModel(
        user_profile_id=user_profile.id,
        movie_id=movie.id,
        rating=data.rating
    )

    db.add(rating)
    await db.commit()
    await db.refresh(rating)

    return MovieRatingResponseSchema.model_validate(rating)


@router.delete("/movies/{movie_id}/delete_rating/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
        movie_id: int,
        user_profile: UserProfileModel = Depends(current_user_profile),
        db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    stmt_rating = await db.execute(select(RatingsModel)
                                   .where(RatingsModel.user_profile_id == user_profile.id,
                                          RatingsModel.movie_id == movie_id))
    rating = stmt_rating.scalar_one_or_none()
    if not rating:
        raise HTTPException(status_code=404, detail="Your rating on this movie not found.")

    await db.delete(rating)
    await db.commit()

    return


add_pagination(router)
