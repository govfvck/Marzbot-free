import math
import random
import uuid
from datetime import datetime as dt
from datetime import timedelta as td
from typing import Literal

from jdatetime import datetime as jdt
from pytz import timezone

import config
from app.logger import get_logger
from app.main import bot
from app.models.user import User

logger = get_logger("utils/helpers")

intervals_en = (
    ("months", 2592000),  # 60 * 60 * 24 * 30
    ("days", 86400),  # 60 * 60 * 24
    ("hours", 3600),  # 60 * 60
    ("minutes", 60),
    ("seconds", 1),
)


intervals_fa = (
    ("ماه", 2592000),  # 60 * 60 * 24 * 30
    ("روز", 86400),  # 60 * 60 * 24
    ("ساعت", 3600),  # 60 * 60
    ("دقیقه", 60),
    ("ثانیه", 1),
)


def hr_time(seconds: int, lang: Literal["en", "fa"] = "en", granularity: int = 2):
    """turns seconds into human readable time"""
    if seconds < 0:
        seconds = 0
    result = []

    intervals = intervals_fa if lang == "fa" else intervals_en
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1 and lang == "en":
                name = name.rstrip("s")
            result.append(f"{int(value)} {name}")
    return " و ".join(result[:granularity])


def hr_date(timestamp: int, format: str = "%Y/%m/%d %H:%M") -> str:
    return jdt.fromtimestamp(timestamp, tz=timezone("Asia/Tehran")).strftime(format)


def get_until_expires(expire_timestamp: int, lang: Literal["en", "fa"] = "en") -> str:
    return hr_time(expire_timestamp - dt.now().timestamp(), lang=lang)


size_names_en = (
    "B",
    "KB",
    "MB",
    "GB",
    "TB",
    "PB",
    "EB",
    "ZB",
    "YB",
)
size_names_fa = (
    "بایت",
    "کیلوبایت",
    "مگابایت",
    "گیگابایت",
    "ترابایت",
    "پتابایت",
    "اگزابایت",
    "زتابایت",
    "یوتابایت",
)


def hr_size(size_bytes: int, lang: Literal["en", "fa"] = "en"):
    size_names = size_names_fa if lang == "fa" else size_names_en
    if size_bytes <= 0:
        return "0"
    size_index = int(math.floor(math.log(size_bytes, 1024)))
    size = round(size_bytes / math.pow(1024, size_index), 2)
    return f"{size:g} {size_names[size_index]}"


async def check_username_exists(username: str) -> bool:
    return await User.filter(username=username).exists()


def generate_random_text(min_length: int = 4, max_length: int = 8) -> str:
    return (str(uuid.uuid4())[: random.randint(min_length, max_length)]).replace(
        "-", ""
    )


async def generate_proxy_username(user: User, max_length: int = 32) -> str:
    username = config.DEFAULT_USERNAME_PREFIX
    if not username.endswith("_"):
        username += "_"
    username += generate_random_text()

    if username.endswith("_"):
        return username[:-1]

    if await check_username_exists(username):
        return await generate_proxy_username(user, max_length)
    return username


def get_expire_timestamp(expire_duration: int) -> int:
    return int((dt.today() + td(seconds=expire_duration)).timestamp())


async def check_force_join(user: User) -> bool:
    for channel_id in config.FORCE_JOIN_CHATS:
        try:
            if (await bot.get_chat_member(channel_id, user.id)).status == "left":
                return False
        except Exception as err:
            logger.error(f"Error checking force_join: {err}")

    user.force_join_check = dt.now()
    await user.save()
    return True
