from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, load_only
from starlette import status

from database import get_db, UserModel, MovieModel, CartItemsModel, CartsModel
from schemas.shopping_cart import CartAddMovieResponseSchema, CartMoviesResponseSchema
from security.auth import get_current_user

router = APIRouter()


@router.post("/add/{movie_id}/", response_model=CartAddMovieResponseSchema, status_code=status.HTTP_201_CREATED)
async def add_movie_to_cart(
        movie_id: int,
        current_user: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    user = await db.get(UserModel, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    existing_movie_in_cart = await db.execute(
        select(CartItemsModel)
        .join(CartsModel)
        .where(CartsModel.user == user,
               CartItemsModel.movie_id == movie_id))
    existing_movie_in_cart = existing_movie_in_cart.scalar_one_or_none()
    if existing_movie_in_cart:
        raise HTTPException(status_code=400, detail="Movie already exists in your cart.")

    cart_item = CartItemsModel(cart_id=user.cart_id,
                               movie_id=movie.id)
    db.add(cart_item)
    await db.commit()

    return CartAddMovieResponseSchema.model_validate(cart_item)


@router.delete("/{movie_id}/delete/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_from_cart(
        movie_id: int,
        current_user: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    user = await db.get(UserModel, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    cart_item = await db.execute(select(CartItemsModel).where(CartItemsModel.cart_id == user.cart_id,
                                                              CartItemsModel.movie_id == movie.id))
    cart_item = cart_item.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Movie not found. Try again later.")
    await db.delete(cart_item)
    await db.commit()
    return


@router.get("/all/", response_model=list[CartMoviesResponseSchema], status_code=status.HTTP_200_OK)
async def list_cart(current_user: int = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)
                    ):
    user = await db.get(UserModel, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    movies_cart = await db.execute(
        select(MovieModel)
        .options(
            load_only(MovieModel.name, MovieModel.price, MovieModel.year),
            selectinload(MovieModel.genres)
        )
        .join(CartItemsModel)
        .where(CartItemsModel.cart_id == user.cart_id)
    )
    movies = movies_cart.scalars().all()
    return [CartMoviesResponseSchema.model_validate(movie) for movie in movies]

