from aiogram import Dispatcher

from app.logger import get_logger

logger = get_logger("handlers")

from . import admin, base, start, user


def include_routers(dp: Dispatcher) -> None:
    for handler in [start, admin, user, base]:
        logger.debug(f"Initializing Handler {handler.__name__!r}")
        if hasattr(handler, "init_handler"):
            handler.init_handler()
        dp.include_router(handler.router)
        logger.debug(f"Router '{handler.router.name}' included!")
