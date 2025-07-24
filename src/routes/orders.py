from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, UserModel, CartsModel, MovieModel, OrdersModel, OrderItemsModel, CartItemsModel
from database.models.movies import PurchasedMoviesModel
from database.models.order import StatusOrderEnum
from schemas.orders import OrderListSchema

from security.auth import get_current_user

router = APIRouter()


@router.post("/create/", response_model=OrderListSchema)
async def create_order(current_user: int = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await db.get(UserModel, current_user)

    cart = await db.execute(
        select(CartsModel)
        .options(joinedload(CartsModel.items).joinedload(CartItemsModel.movie))
        .where(CartsModel.user == user)
    )
    cart = cart.scalars().first()
    if cart is None:
        raise HTTPException(status_code=400, detail="You don't have any movies in your cart yet.")

    # All available films in cart
    movies_id = [item.movie.id for item in cart.items if item.movie.available]

    # All films what is purchased before
    purchased_movies = await db.execute(
        select(PurchasedMoviesModel.c.movie_id).where(
            and_(
                PurchasedMoviesModel.c.user_id == user.id,
                PurchasedMoviesModel.c.movie_id.in_(movies_id))
        )
    )
    purchased_movies = purchased_movies.scalars().all()

    movies_id_to_buy = set(movies_id).difference(set(purchased_movies))

    if not movies_id_to_buy:
        raise HTTPException(status_code=400, detail="All movies from your cart already are bought.")

    pending_movies = await db.execute(
        select(OrdersModel)
        .options(selectinload(OrdersModel.items).selectinload(OrderItemsModel.movie))
        .where(
            and_(OrdersModel.user_id == user.id,
                 OrdersModel.status == StatusOrderEnum.pending,
                 OrderItemsModel.movie_id.in_(movies_id_to_buy))
        )
    )
    pending_movies = pending_movies.unique().scalars().all()

    pending_movies_id = []
    for order_items in pending_movies:
        for item in order_items.items:
            pending_movies_id.append(item.movie_id)

    movies_id_to_buy = movies_id_to_buy.difference(pending_movies_id)
    if not movies_id_to_buy:
        raise HTTPException(status_code=400, detail=f"You don't have new movies in your cart yet. "
                                                    f"In pending status you have {len(pending_movies_id)} movies.")
    movies = await db.execute(select(MovieModel)
                              .where(MovieModel.id.in_(list(movies_id_to_buy))))
    movies = movies.scalars().all()

    order_movies = []
    total_amount = 0
    try:
        order = OrdersModel(
            user_id=user.id,
            status=StatusOrderEnum.pending,
            total_amount=0
        )
        db.add(order)
        await db.flush()

        for movie in movies:
            total_amount += movie.price
            order_movies.append({
                "order_id": order.id,
                "movie_id": movie.id,
                "price_at_order": movie.price
            })

        order.total_amount = total_amount

        if order_movies:
            await db.execute(
                insert(OrderItemsModel),
                order_movies
            )
        await db.commit()

        response = {"time_order": order.created_at,
                    "movies": movies,
                    "total_amount": total_amount,
                    "order_status": StatusOrderEnum.pending}
        return OrderListSchema.model_validate(response)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
