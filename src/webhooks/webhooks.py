from fastapi import HTTPException, Depends, Request, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from config.settings import Settings
from database import get_db, PaymentsModel, OrdersModel, PaymentStatusEnum, StatusOrderEnum

router = APIRouter()

settings = Settings()


@router.post("/webhooks/")
async def stripe_webhook(
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_successful_payment(session, db)

    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        await handle_expired_payment(session, db)

    return {"status": "success"}


async def handle_successful_payment(session, db: AsyncSession):
    order_id = int(session['metadata']['order_id'])
    payment_intent_id = session['payment_intent']

    stmt = select(PaymentsModel).where(
        PaymentsModel.order_id == order_id,
        PaymentsModel.status == PaymentStatusEnum.pending
    )
    result = await db.execute(stmt)
    payment = result.scalars().first()

    if payment:
        payment.status = PaymentStatusEnum.successful
        payment.external_payment_id = payment_intent_id
        stmt_order = select(OrdersModel).where(OrdersModel.id == order_id)
        result_order = await db.execute(stmt_order)
        order = result_order.scalars().first()

        if order:
            order.status = StatusOrderEnum.paid

        await db.commit()


async def handle_expired_payment(session, db: AsyncSession):
    order_id = int(session['metadata']['order_id'])

    stmt = select(PaymentsModel).where(
        PaymentsModel.order_id == order_id,
        PaymentsModel.status == PaymentStatusEnum.pending
    )
    result = await db.execute(stmt)
    payment = result.scalars().first()

    if payment:
        payment.status = PaymentStatusEnum.canceled
        await db.commit()
