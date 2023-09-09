from aiogram import Dispatcher
from aiohttp import web

import config
from app.logger import get_logger

logger = get_logger("webapp")
webapp = web.Application()
webapp_runner: web.TCPSite = None


async def on_startup() -> web.TCPSite:
    from . import payment

    webapp.add_routes(payment.routes)
    runner = web.AppRunner(webapp)
    await runner.setup()
    global webapp_runner
    webapp_runner = web.TCPSite(
        runner, host=config.WEBAPP_HOST, port=config.WEBAPP_PORT
    )
    await webapp_runner.start()


async def on_shutdown() -> None:
    await webapp_runner.stop()


def setup_webapp(dp: Dispatcher) -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
