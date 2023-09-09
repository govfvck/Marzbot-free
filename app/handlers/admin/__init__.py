import importlib

from aiogram import Router

from app.logger import get_logger

router = Router(name="admin")
logger = get_logger("handlers/admin")

handlers = [
    "admin",
    "user",
    "server",
    "service",
    "setting",
]


def init_handler() -> None:
    for name in handlers:
        importlib.import_module(f".{name}", "app.handlers.admin")
