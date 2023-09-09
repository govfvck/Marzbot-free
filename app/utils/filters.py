from datetime import datetime as dt
from datetime import timedelta as td
from typing import Any

from aiogram.filters import Filter
from aiogram.types import Message

import config
from app.keyboards.base import ForceJoin
from app.main import bot
from app.middlewares.acl import current_user
from app.models.user import User
from app.utils import helpers


class SuperUserAccess(Filter):
    async def __call__(self, message: Message) -> bool:
        return current_user.get().super_user


class IsJoinedToChannel(Filter):
    def __init__(self, send_alert: bool = True) -> None:
        self.send_alert = send_alert

    async def __call__(self, message: Message) -> bool:
        user = current_user.get()
        if user.force_join_check and (
            dt.now() - user.force_join_check.replace(tzinfo=None)
        ) < td(hours=24):
            return True
        if await helpers.check_force_join(user=user):
            return True
        if self.send_alert:
            await bot.send_message(
                user.id, config.FORCE_JOIN_TEXT, reply_markup=ForceJoin().as_markup()
            )
        return False
