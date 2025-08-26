from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.requests import Request

from database import get_db, OrdersModel, OrderItemsModel, PaymentsModel, PaymentsItemsModel
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
        request: Request,
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

    payment = PaymentsModel(
        user_id=current_user,
        order_id=order.id,
        amount=0,
    )
    db.add(payment)
    await db.flush()

    payment_items = [
        {"payment_id": payment.id,
         "order_item_id": item.id,
         "price_at_payment": item.price_at_order}
        for item in order.items
    ]
    await db.execute(insert(PaymentsItemsModel).values(payment_items))
    final_price = sum([k.get("price_at_payment") for k in payment_items])

    payment.amount = final_price

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
            metadata={"order_id": str(order.id)},
            mode="payment",
            success_url=f"{request.base_url}api/payments/success/{order.id}/",
            cancel_url=f"{request.base_url}api/payments/cancel/{order.id}/",
        )
        await db.commit()
        return session
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))
