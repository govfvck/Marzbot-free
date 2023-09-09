from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.user import proxy
from app.models.user import User


class UserPanelAction(str, Enum):
    show = "show"
    charge = "charge"
    proxies = "proxies"
    settings = "settings"


class UserPanel(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="account"):
        action: UserPanelAction

    def __init__(self, user: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text="💳 شارژ حساب",
            callback_data=self.Callback(action=UserPanelAction.charge),
        )
        self.button(
            text="📍 اشتراک‌های من",
            callback_data=self.Callback(action=UserPanelAction.proxies),
        )
        self.adjust(1, 1)
