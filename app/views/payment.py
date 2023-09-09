import hashlib
import hmac
import json
from datetime import datetime as dt

from aiohttp import web
from tortoise.transactions import in_transaction

import config
from app.main import bot
from app.models.user import CryptoPayment, Transaction
from payment_clients.nowpayments import PaymentResponse

from . import logger

routes = web.RouteTableDef()


def hmac_sign(key: str, data: dict) -> str:
    """
    sort the post data from nowpayments and sign it with the secret key and sha512
    """
    return hmac.new(
        key.encode(),
        json.dumps(dict(sorted(data.items())), separators=(",", ":")).encode(),
        hashlib.sha512,
    ).hexdigest()


def verify_signature(sig: str, key: str, data: dict) -> bool:
    if sig == hmac_sign(key, data):
        return True
    return False


@routes.post("/npipn/")
async def verify_payment(request: web.Request):
    if not request.can_read_body:
        return
    data = await request.json()
    logger.info(f"got ipn from nowpayments: {data}")
    if config.NP_IPN_SECRET_KEY:
        nowpayments_sig = request.headers.get("x-nowpayments-sig")
        if not verify_signature(nowpayments_sig, config.NP_IPN_SECRET_KEY, data):
            return

    payment = PaymentResponse(**data)
    async with in_transaction():
        transaction = (
            await Transaction.filter(id=payment.order_id)
            .prefetch_related("crypto_payment")
            .first()
        )
        if not transaction:
            return

        if payment.payment_status == "finished" and (
            transaction.status
            not in [Transaction.Status.finished, Transaction.Status.partially_paid]
        ):
            transaction.status = Transaction.Status.finished
            transaction.finished_at = dt.now()
            transaction.amount_paid = (
                transaction.crypto_payment.usdt_rate * payment.price_amount
            )
            await transaction.save()
            await transaction.refresh_from_db()
            await transaction.crypto_payment.update_from_dict(
                {
                    "pay_currency": payment.pay_currency,
                    "pay_amount": payment.pay_amount,
                    "nowpm_updated_at": payment.updated_at,
                    "payment_status": CryptoPayment.PaymentStatus.finished,
                    "outcome_amount": payment.outcome_amount,
                    "outcome_currency": payment.outcome_currency,
                    "purchase_id": payment.purchase_id,
                    "pay_address": payment.pay_address,
                }
            ).save()
            text = f"""
✅ پرداخت شما از طریق ارز دیجیتال با موفقیت تأیید شد و مبلغ <b>{transaction.amount:,}</b> تومان به حساب شما اضافه شد!

💳 شماره فاکتور: <b>{transaction.id}</b>
💴 مبلغ پرداختی: <b>{transaction.amount_paid:,}</b> تومان
‌‌
"""
            await bot.send_message(transaction.user_id, text)

    return web.Response(status=200)
