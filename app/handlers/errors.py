from aiogram import Router

from app.logger import get_logger

router = Router(name="erros")
logger = get_logger("handlers/errors")


# @router.errors()
# async def httpx_error_handler(exception: httpx.ConnectError | httpx.ConnectTimeout):
#     raise exception
