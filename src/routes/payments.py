from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.responses import RedirectResponse

from database import get_db, OrdersModel, OrderItemsModel
import stripe

from security.auth import get_current_user
from config.settings import Settings

router = APIRouter()

settings = Settings()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.get("/success/{order_id}/")
async def success_payment(order_id: int):
    return {"message": f"Your payment has been successfully processed!. Id order: {order_id}"}


@router.get("/cancel/{order_id}/")
async def cancel_payment(order_id: int):
    return {"message": f"Your payment cancelled. Id order: {order_id}"}


@router.post("/{id_order}/create/")
async def create_payment(
        id_order: int,
        current_user: int = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    stmt = await db.execute(
        select(OrdersModel).options(selectinload(OrdersModel.items).joinedload(OrderItemsModel.movie))
        .where(OrdersModel.id == id_order,
               OrdersModel.user_id == current_user))
    order = stmt.scalars().one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found. Payment not started.")
    try:
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price_data': {
                        'currency': 'uah',
                        'product_data': {
                            'name': item.movie.name,
                        },
                        'unit_amount': round(item.price_at_order * 100),
                    },
                    'quantity': 1,
                }
                for item in order.items
            ],
            metadata={"order_id": order.id, "user_id": current_user},
            mode="payment",
            success_url=f"http://localhost:8000/api/payments/success/{order.id}/",
            cancel_url=f"http://localhost:8000/api/payments/cancel/{order.id}/",
        )
        return RedirectResponse(session["url"], status_code=status.HTTP_302_FOUND)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))
