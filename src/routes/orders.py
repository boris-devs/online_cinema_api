from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, UserModel, CartsModel, MovieModel, OrdersModel, OrderItemsModel, CartItemsModel
from database.models.movies import PurchasedMoviesModel
from database.models.order import StatusOrderEnum
from schemas.orders import OrderCreateSchema, OrdersUsersModeratorResponseSchema, OrdersUserListSchema

from security.auth import get_current_user

router = APIRouter()


@router.post("/create/", response_model=OrderCreateSchema)
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

    if not movies:
        raise HTTPException(400, detail="In current time you dont have any movies what you could add in order.")

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

        response = {"created_at": order.created_at,
                    "movies": movies,
                    "total_amount": total_amount,
                    "status": StatusOrderEnum.pending}
        return OrderCreateSchema.model_validate(response)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my/", response_model=list[OrdersUserListSchema])
async def user_list_orders(
        current_user: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    user_orders = await db.execute(select(OrdersModel).where(OrdersModel.user_id == current_user))
    user_orders = user_orders.scalars().all()
    return [OrdersUserListSchema.model_validate(order) for order in user_orders]


@router.get("/{id_order}/")
async def get_order(
        id_order: int,
        current_user: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(OrdersModel).where(OrdersModel.id == id_order,
                                                       OrdersModel.user_id == current_user))
    current_order = query.scalars().first()
    return current_order


@router.get("/", response_model=list[OrdersUsersModeratorResponseSchema])
async def list_orders_users_by_moderator(
        user_email: Optional[str] = Query(None, description="Filter by user email"),
        order_date_from: Optional[datetime] = Query(None, description="Start date for order filtering"),
        order_date_to: Optional[datetime] = Query(None, description="End date for order filtering"),
        status_order: Optional[str] = Query(None, description="Order status filter"),
        current_user: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    moderator_user = await db.execute(select(UserModel).where(UserModel.id == current_user)
                                      .options(joinedload(UserModel.group)))

    moderator_user = moderator_user.scalar_one_or_none()
    if moderator_user.group.name != "moderator":
        raise HTTPException(status_code=401,
                            detail="You do not have permissions for this action.")

    query = (
        select(OrdersModel)
        .join(UserModel)
        .options(
            selectinload(OrdersModel.items).load_only(
                OrderItemsModel.id,
                OrderItemsModel.movie_id
            ).selectinload(OrderItemsModel.movie)
        )
    )

    if user_email:
        query = query.where(UserModel.email == user_email)
    if order_date_from:
        query = query.where(OrdersModel.created_at >= order_date_from)
    if order_date_to:
        query = query.where(OrdersModel.created_at <= order_date_to)
    if status_order:
        query = query.where(OrdersModel.status == status_order)

    query = await db.execute(query)
    orders = query.scalars().all()
    return [OrdersUsersModeratorResponseSchema.model_validate(order) for order in orders]
