from aiogram import Dispatcher

from .acl import ACLMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.outer_middleware(ACLMiddleware())
