from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import add_pagination, Page
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import selectinload

from database.models.movies import MovieModel
from schemas import MovieListSchema
from database import get_db
from schemas.movies import MovieDetailSchema

router = APIRouter()


@router.get("/movies/", response_model=Page[MovieListSchema])
async def get_movies(db: AsyncSession = Depends(get_db)):
    return await paginate(db, select(MovieModel).order_by(MovieModel.year))


@router.get("/movies/detail/{id_film}/", response_model=MovieDetailSchema)
async def get_movie_detail(id_film: int, db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(select(MovieModel)
                            .where(MovieModel.id == id_film)
                            .options(selectinload(MovieModel.genres),
                                     selectinload(MovieModel.stars),
                                     selectinload(MovieModel.directors)))
    result = stmt.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail="Movie not found.")

    return MovieDetailSchema.model_validate(result)


add_pagination(router)
