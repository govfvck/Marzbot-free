import config
from app.logger import get_logger
from app.main import bot
from app.models.user import CryptoPayment

logger = get_logger("payment_logs")


async def send_perfect_money_log(
    user_id: int,
    ev_number: int,
    ev_code: int,
    ev_amount: int,
    ev_amount_currency: str,
    payee_account: str,
    payment_batch_number: str,
    toman_amount: int,
    user_balance_before: int,
    user_balance_after: int,
) -> None:
    logger.info(
        f"Perfectmoney Payment Log [{user_id}]: {ev_number=}, "
        f"{ev_code=}, "
        f"{ev_amount=}, "
        f"{ev_amount_currency=}, "
        f"{payee_account=}, "
        f"{payment_batch_number=}, "
        f"{toman_amount=}"
        f"{user_balance_before=}, "
        f"{user_balance_after=}"
    )
    text = f"""
#perfectmoney #payment


user_id: <code>{user_id}</code>
ev number: <code>{ev_number}</code>
ev code: <code>{ev_code}</code>
ev currency: <b>{ev_amount_currency}</b>
payee account: <code>{payee_account}</code>
payment batch number: <code>{payment_batch_number}</code>
amound in tomans: <b>{toman_amount}</b>
user balance before: <b>{user_balance_before}</b>
user balance after: <b>{user_balance_after}</b>
    """
    await bot.send_message(config.TRANSACTION_LOGS, text)


async def send_crypto_payment_log(db_payment: CryptoPayment) -> None:
    text = f"""
#crypto #payment #{db_payment.coin}

user_id: <code>{db_payment.user_id}</code>
id: <code>{db_payment.id}</code>
usd rate: <code>{db_payment.usd_rate}</code>
payment_id: <code>{db_payment.usd_rate}</code>
payment_status: <code>{db_payment.payment_status}</code>
pay_address: <code>{db_payment.pay_address}</code>
price_amount: <code>{db_payment.price_amount}</code>
pay_amount: <code>{db_payment.pay_amount}</code>
purchase_id: <code>{db_payment.purchase_id}</code>
amount_received: <code>{db_payment.amount_received}</code>
outcome_amount: <code>{db_payment.outcome_amount}</code>
outcome_currency: <code>{db_payment.outcome_currency}</code>
    """
    await bot.send_message(config.TRANSACTION_LOGS, text)
