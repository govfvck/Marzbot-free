from aiogram import Dispatcher
from tortoise import Tortoise
from tortoise.fields import DatetimeField
from tortoise.models import Model

import config

db = Tortoise()


class Base(Model):
    class Meta:
        abstract = True


class TimedBase(Base):
    class Meta:
        abstract = True

    created_at = DatetimeField(null=True, auto_now_add=True)
    updated_at = DatetimeField(null=True, auto_now=True)


class CreatedTimeBase(Base):
    class Meta:
        abstract = True

    created_at = DatetimeField(null=True, auto_now_add=True)


async def on_startup():
    await db.init(config=config.TORTOISE_ORM)


async def on_shutdown():
    await db.close_connections()


def setup_database(dp: Dispatcher):
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
