from typing import Iterable

import config
from app.main import redis


class Settings:
    @classmethod
    async def _get(cls, key: str) -> tuple[bool, bool]:
        """Returns value of a settings field

        Args:
            key (str): settings key

        Returns:
            tuple[bool, bool]: first value is the result and second one is the True if it's fetched from redis
        """
        if (res := await redis.get(f"SETTINGS:{key}")) is not None:
            return bool(int(res)), True
        return config.SETTINGS.get(key), False

    @classmethod
    async def _set(cls, key: str, value: bool) -> bool | None:
        """Sets value of a settings field

        Args:
            key (str): settings key

        Returns:
            bool | None:  result of redis.set
        """
        return await redis.set(f"SETTINGS:{key}", int(value))

    @classmethod
    async def bot_access_only(cls) -> bool:
        return (await cls._get("BOT:ACCESS_ONLY"))[0]

    @classmethod
    async def set_bot_access_only(cls, value: bool) -> None:
        await cls._set("BOT:ACCESS_ONLY", value)

    @classmethod
    async def user_has_access(cls, user_id: int | str) -> bool:
        return bool((await redis.smismember("SETTINGS:HAS_ACCESS_USERS", [user_id]))[0])

    @classmethod
    async def give_user_access(cls, user_id: int | str) -> int:
        return await redis.sadd("SETTINGS:HAS_ACCESS_USERS", user_id)

    @classmethod
    async def remove_user_access(cls, user_id: int | str) -> int:
        return await redis.srem("SETTINGS:HAS_ACCESS_USERS", user_id)

    @classmethod
    async def bot_referral_system(cls) -> bool:
        return (await cls._get("BOT:REFERRAL_SYSTEM"))[0]

    @classmethod
    async def set_bot_referral_system(cls, value: bool) -> None:
        await cls._set("BOT:REFERRAL_SYSTEM", value)

    # payment settings
    @classmethod
    async def payment_crypto(cls) -> bool:
        return (await cls._get("PAYMENT:CRYPTO"))[0]

    @classmethod
    async def set_payment_crypto(cls, value: bool) -> None:
        await cls._set("PAYMENT:CRYPTO", value)

    @classmethod
    async def payment_card_to_card(cls) -> bool:
        return (await cls._get("PAYMENT:CARD_TO_CARD"))[0]

    @classmethod
    async def set_payment_card_to_card(cls, value: bool) -> None:
        await cls._set("PAYMENT:CARD_TO_CARD", value)

    @classmethod
    async def payment_rial_gateway(cls) -> bool:
        return (await cls._get("PAYMENT:RIAL_GATEWAY"))[0]

    @classmethod
    async def set_payment_rial_gateway(cls, value: bool) -> None:
        await cls._set("PAYMENT:RIAL_GATEWAY", value)

    @classmethod
    async def payment_perfect_money(cls) -> bool:
        return (await cls._get("PAYMENT:PERFECT_MONEY"))[0]

    @classmethod
    async def set_payment_perfect_money(cls, value: bool) -> None:
        await cls._set("PAYMENT:PERFECT_MONEY", value)

    @classmethod
    async def _get_settings(cls, keys: Iterable[str]) -> dict[str, bool]:
        """Update Settings values and return

        Returns:
            dict[str, bool]: returns a copy of settings dict in config.SETTINGS with updated values from redis db
        """
        setts = dict()
        for key in keys:
            setts[key], _ = await cls._get(key)
        return setts

    @classmethod
    async def settings(cls) -> dict[str, bool]:
        return await cls._get_settings(keys=config.SETTINGS.keys())

    @classmethod
    async def payment_settings(cls) -> dict[str, bool]:
        return await cls._get_settings(
            keys=[key for key in config.SETTINGS.keys() if key.startswith("PAYMENT:")]
        )

    @classmethod
    async def reset_to_default_settings(cls) -> None:
        """Deletes all saved settings from redis db"""
        await redis.delete(*[f"SETTINGS:{key}" for key in config.SETTINGS])
