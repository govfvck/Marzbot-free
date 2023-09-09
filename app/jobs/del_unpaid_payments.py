from datetime import datetime as dt
from datetime import timedelta as td

from tortoise.expressions import Q

from app.jobs import logger
from app.main import scheduler
from app.models.user import Transaction


async def delete_unpaid_payments():
    unpaid_transactions = Transaction.filter(
        ~Q(status=Transaction.Status.finished | Transaction.Status.partially_paid),
        created_at__lt=dt.utcnow() - td(days=14),
    )
    if (count := await unpaid_transactions.count()) < 1:
        return
    logger.info(f"Deleting {count} unpaid transactions...")
    await unpaid_transactions.delete()


scheduler.add_job(
    delete_unpaid_payments,
    "interval",
    hours=24,
    id="delete_unpaid_payments",
    replace_existing=True,
    start_date=dt.utcnow() + td(seconds=10),
)
