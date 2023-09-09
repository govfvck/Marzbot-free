from datetime import datetime as dt

import httpx

BASE_URL = "https://api.nobitex.ir/market"

DEFAULT_HEADERS = {"content-type": "application/json"}


class CouldNotGetUSDTPrice(Exception):
    pass


class NobitexMarketAPI:
    cached_price: int = None
    last_cached: int = None
    cached_trx_price: int = None
    last_cached_trx: int = None

    @classmethod
    async def _call_api(
        cls,
        method: str,
        json: dict[str, str],
        headers: dict[str, str] = DEFAULT_HEADERS,
    ):
        url = BASE_URL.rstrip("/") + method
        async with httpx.AsyncClient(headers=headers) as client:
            r = await client.post(url, json=json)
            if r.status_code == 200:
                return r.json()

    @classmethod
    async def get_price(cls, use_cache: bool = True) -> int:
        """Fetch latest usdttrc20 price from Nobitex

        the price will be cached for 5 minutes
        """
        if use_cache and cls.cached_price:
            if not cls.last_cached or (
                cls.last_cached - dt.now().timestamp() > 5
            ):  # fine minute cache
                return await cls.get_price(use_cache=False)
            return cls.cached_price

        r = await cls._call_api(
            "/stats", json={"dstCurrency": "rls", "srcCurrency": "usdt"}
        )
        if r:
            usdt_rls = r.get("stats").get("usdt-rls")
            cls.cached_price = int(int(usdt_rls.get("latest")) / 10)
            cls.last_cached = dt.now().timestamp()
            return cls.cached_price
        else:
            raise CouldNotGetUSDTPrice("could not fetch usdt price from nobitex")

    @classmethod
    async def get_trx_price(cls, use_cache: bool = True) -> int:
        """Fetch latest trx price from Nobitex

        the price will be cached for 5 minutes
        """
        if use_cache and cls.cached_trx_price:
            if not cls.last_cached_trx or (
                cls.last_cached_trx - dt.now().timestamp() > 5
            ):  # five minute cache
                return await cls.get_price(use_cache=False)
            return cls.cached_trx_price

        r = await cls._call_api(
            "/stats", json={"dstCurrency": "rls", "srcCurrency": "trx"}
        )
        if r:
            trx_rls = r.get("stats").get("trx-rls")
            cls.cached_trx_price = int(int(trx_rls.get("latest")) / 10)
            cls.last_cached_trx = dt.now().timestamp()
            return cls.cached_trx_price
        else:
            raise CouldNotGetUSDTPrice("could not fetch usdt price from nobitex")
