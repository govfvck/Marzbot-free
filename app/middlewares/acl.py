from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Awaitable, Callable, Iterator

from aiogram import BaseMiddleware, types

from app.logger import get_logger
from app.models.user import User
from app.utils.settings import Settings

logger = get_logger(__name__)


current_user: ContextVar[User] = ContextVar("current_user", default=None)


class ACLMiddleware(BaseMiddleware):
    """ACL middleware for user setup"""

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        logger.debug(f"New event: {event}")
        logger.debug(f"New event data: {data}")
        user: types.User = data["event_from_user"]
        if await self.setup_chat(data, user):
            with self.context(user=data["user"]):
                return await handler(event, data)

    @contextmanager
    def context(self, user: User) -> Iterator[None]:
        """Set current_user context"""
        ctx_token = current_user.set(user)
        logger.debug(f"Setting up user with {user.id=} and {ctx_token=}")
        try:
            yield
        finally:
            logger.debug(f"Resetting user with {user.id=} and {ctx_token=}")
            current_user.reset(ctx_token)

    async def setup_chat(self, data: dict[str, Any], user: types.User) -> User | None:
        db_user = await User.filter(id=user.id).first()
        if not db_user:
            if await Settings.bot_access_only() and not (
                await Settings.user_has_access(user_id=user.id)
            ):
                return
            db_user = await User.create(
                id=user.id, username=user.username, full_name=user.full_name
            )

        update = dict()
        if user.username is not None and user.username != db_user.username:
            update.update({"username": user.username})
        if user.full_name is not None and user.full_name != db_user.name:
            update.update({"name": user.full_name})
        if update:
            await db_user.update_from_dict(update).save()
            await db_user.refresh_from_db()

        data["user"] = db_user
        return db_user
