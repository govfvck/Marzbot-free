from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .admin import AdminPanel, AdminPanelAction


class SettingsActions(str, Enum):
    flip_access_only = "access_only"
    flip_referral_system = "referral_system"
    flip_payment_crypto = "payment_crypto"
    flip_payment_card_to_card = "payment_card_to_card"
    flip_payment_perfect_money = "payment_perfect_money"
    flip_payment_rial_gateway = "payment_rial_gateway"


class SettingsKeyboard(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="setngs"):
        action: SettingsActions
        confirmed: bool = False

    def __init__(self, settings: dict[str, bool], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text=f"Access Only: {'✅' if settings.get('BOT:ACCESS_ONLY') else '❌'}",
            callback_data=self.Callback(action=SettingsActions.flip_access_only),
        )
        self.button(
            text=f"Crypto Payment: {'✅' if settings.get('PAYMENT:CRYPTO') else '❌'}",
            callback_data=self.Callback(action=SettingsActions.flip_payment_crypto),
        )
        self.button(
            text="Back",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.panel),
        )
        self.adjust(1, 1)


class ConfirmSettings(InlineKeyboardBuilder):
    def __init__(self, action: SettingsActions, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text="Confirm",
            callback_data=SettingsKeyboard.Callback(action=action, confirmed=True),
        )

        self.button(
            text="Cancel",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.settings),
        )
        self.adjust(1, 1)
