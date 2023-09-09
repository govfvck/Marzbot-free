from datetime import datetime as dt
from typing import Any, Literal

import httpx
from pydantic import BaseModel

import config

DEFAULT_HEADERS = {
    "x-api-key": config.NP_API_KEY,
}


def get_parsed_query_parameters(data: dict[str, str]) -> str:
    return "&".join(
        [f"{key}={value}" for key, value in data.items() if value is not None]
    )


class NowPaymentsError(Exception):
    pass


class MinAmountResponse(BaseModel):
    currency_from: str
    currency_to: str
    min_amount: float
    fiat_equivalent: float


class PaymentResponse(BaseModel):
    payment_id: int | str
    payment_status: str
    pay_address: str
    price_amount: float
    price_currency: str
    pay_amount: float
    pay_currency: str
    order_id: int
    created_at: dt | None = None
    updated_at: dt | None = None
    purchase_id: str | None = None
    amount_received: float | None = None
    network: str | None = None
    network_percision: int | None = None
    expiration_estimate_date: dt | None = None
    outcome_amount: float | None = None
    outcome_currency: str | None = None


class CreateInvoiceResponse(BaseModel):
    id: str
    order_id: str
    order_description: str | None = None
    price_amount: float
    price_currency: str
    pay_currency: str | None = None
    ipn_callback_url: str
    invoice_url: str
    success_url: str | None = None
    cancel_url: str | None = None
    created_at: dt
    updated_at: dt


class NowPaymentsAPI:
    @classmethod
    async def _call_api(
        cls,
        method: Literal["GET", "POST"],
        path: str,
        headers: dict[str, str] = DEFAULT_HEADERS,
        get_data: dict[str, Any] = None,
        post_data: dict[str, Any] = None,
    ):
        if headers.get("x-api-key") is None:
            raise NowPaymentsError("Nowpayments Api key is not defined!")
        async with httpx.AsyncClient(headers=headers) as client:
            url = config.NP_API_URL + path
            if method == "GET":
                if get_data:
                    url = url + "?" + get_parsed_query_parameters(data=get_data)
                r = await client.get(url=url)
                if r.status_code == 200:
                    return r.json()
            elif method == "POST":
                r = await client.post(url=url, json=post_data)
                print(r.text)
                print(r.status_code)
                if r.status_code in {200, 201}:
                    return r.json()
                else:
                    raise NowPaymentsError(f"{r.text}")

    @classmethod
    async def status(cls) -> bool:
        r = await cls._call_api(
            "GET",
            "/status",
            headers=dict(**DEFAULT_HEADERS),
        )
        if r:
            if r.get("message") == "OK":
                return True
        return False

    @classmethod
    async def create_invoice(
        cls,
        price_amount: float,
        order_id: int,
        order_description: str = "",
        price_currency: str = "usd",
        ipn_callback_url: str = config.NP_IPN_CALLBACK_URL,
        success_url: str = config.NP_SUCCESS_URL,
        cancel_url: str = config.NP_CANCEL_URL,
    ):
        data = {
            "price_amount": price_amount,
            "price_currency": price_currency,
            "order_id": order_id,
            "order_description": order_description,
            "ipn_callback_url": ipn_callback_url,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "is_fee_paid_by_user": False if price_amount < 2.7 else True,
        }
        r = await cls._call_api(
            "POST",
            "/invoice",
            headers=dict(**DEFAULT_HEADERS, **{"Content-Type": "application/json"}),
            post_data=data,
        )
        return CreateInvoiceResponse(**r)

    @classmethod
    async def create_payment(
        cls,
        price_amount: float,
        pay_currency: str,
        order_id: int,
        price_currency: str = "usd",
        ipn_callback_url: str = config.NP_IPN_CALLBACK_URL,
    ) -> PaymentResponse:
        data = {
            "price_amount": price_amount + (price_amount * 0.005),
            "pay_currency": pay_currency,
            "price_currency": price_currency,
            "ipn_callback_url": ipn_callback_url,
            "order_id": order_id,
        }
        r = await cls._call_api(
            "POST",
            "/payment",
            headers=dict(**DEFAULT_HEADERS, **{"Content-Type": "application/json"}),
            post_data=data,
        )
        return PaymentResponse(**r)

    @classmethod
    async def get_payment_status(cls, payment_id: str) -> PaymentResponse:
        r = await cls._call_api("GET", f"/payment/{payment_id}")
        return PaymentResponse(**r)

    @classmethod
    async def get_minimum_amount(
        cls, currency_from: str, currency_to: str, fiat_equivalent: str = "usd"
    ) -> MinAmountResponse:
        r = await cls._call_api(
            "GET",
            "/min-amount",
            get_data={
                "currency_from": currency_from,
                "currency_to": currency_to,
                "fiat_equivalent": fiat_equivalent,
            },
        )
        return MinAmountResponse(**r)
