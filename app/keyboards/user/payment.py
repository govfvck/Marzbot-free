from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config
from app.keyboards.user.account import UserPanel, UserPanelAction

# from app.models.user import TrxSwapPayment


class ChargeMethods(str, Enum):
    crypto = "crypto"
    perfectmoney = "perfectmoney"
    card_to_card = "card_to_card"
    rial_gateway = "rial_gateway"


class ChargePanel(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="payment"):
        method: ChargeMethods

    def __init__(self, settings: dict[str, bool], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if settings.get("PAYMENT:CRYPTO"):
            self.button(
                text="💸 ارز دیجیتال",
                callback_data=self.Callback(method=ChargeMethods.crypto),
            )
        self.adjust(1, 1, 1)


class SelectPayAmount(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="payslctam"):
        amount: int
        free: int = 0
        method: ChargeMethods

    def __init__(self, method: ChargeMethods, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        amount_list = [
            20_000,
            50_000,
            75_000,
            95_000,
            130_000,
            195_000,
            275_000,
            330_000,
            400_000,
            600_000,
        ]
        for amount in amount_list:
            free = int(
                0
                if (not config.PAYMENTS_DISCOUNT_ON)
                or (amount < config.PAYMENTS_DISCOUNT_ON)
                else amount * (config.PAYMENTS_DISCOUNT_ON_PERCENT / 100)
            )
            self.button(
                text=f"{amount:,} تومان"
                if not free
                else f"{free:,} 🔥 + {amount:,} تومان",
                callback_data=self.Callback(amount=amount, free=free, method=method),
            )
        self.button(
            text="✍️ مبلغ دلخواه",
            callback_data=self.Callback(amount=0, method=method),
        )

        self.button(
            text="🔙 برگشت",
            callback_data=UserPanel.Callback(action=UserPanelAction.charge),
        )
        self.adjust(2, 2, 2, 2, 1, 1, 1)


class PayCryptoUrl(InlineKeyboardBuilder):
    def __init__(self, url: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(text="💳 پرداخت", url=url)
