import importlib

from aiogram import Router

from app.logger import get_logger

router = Router(name="user")
logger = get_logger("handlers/user")

handlers = [
    # "user",
    "account",
    "payment",
    "purchase",
    "proxy",
]


def init_handler() -> None:
    for name in handlers:
        importlib.import_module(f".{name}", "app.handlers.user")
