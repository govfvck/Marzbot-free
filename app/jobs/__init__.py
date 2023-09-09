from app.logger import get_logger

logger = get_logger("jobs")


from app.jobs import del_unpaid_payments  # noqa
