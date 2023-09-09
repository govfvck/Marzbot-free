from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio.client import Redis

import config
from app.logger import get_logger

redis = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,
)  # because it is used as the fsm_storage, it will be closed automatically on shutdown

storage = RedisStorage(
    redis=redis,
    state_ttl=600,
    data_ttl=600,
)

dp = Dispatcher(storage=storage)
aiohttp_session = AiohttpSession(proxy=config.PROXY)
bot = Bot(token=config.BOT_TOKEN, session=aiohttp_session, parse_mode=config.PARSE_MODE)
bot_username = config.BOT_USERNAME

scheduler = AsyncIOScheduler(
    jobstores={
        "default": RedisJobStore(
            db=config.REDIS_DB, host=config.REDIS_HOST, port=config.REDIS_PORT
        )
    },
    executors={"default": AsyncIOExecutor()},
    job_defaults={
        "coalesce": True,  # Trigger only one job to make up for missed jobs.
        "max_instances": 5,
    },
    timezone="UTC",
)

logger = get_logger("marzbot")


def get_bot_username() -> str:
    return bot_username


async def on_startup():
    global bot_username
    bot_username = (await bot.get_me()).username
    scheduler.start()


async def on_shutdown():
    scheduler.shutdown()


def main() -> None:
    logger.info("Configuring Database...")
    from app.models import setup_database

    setup_database(dp)
    logger.info("DataBase configuration Done!")

    logger.info("Configuring Routers...")
    from app.handlers import include_routers

    include_routers(dp)
    logger.info("Routers included successfully!")

    logger.info("Setting up middlewares...")
    from app.middlewares import setup_middlewares

    setup_middlewares(dp)
    logger.info("Middlewares setup successfully!")

    logger.info("Setting up API servers...")
    from app.marzban import setup_api

    setup_api(dp)
    logger.info("Setup API servers successfully!")

    logger.info("Setting up webapp...")
    from app.views import setup_webapp

    setup_webapp(dp)
    logger.info("Setup webapp successfully!")

    logger.info("Setting up scheduled jobs...")

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    logger.info("Setup scheduled jobs successfully!")

    logger.info("Starting polling for updates...")
    dp.run_polling(bot)
