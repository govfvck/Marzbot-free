from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.user.account import UserPanel, UserPanelAction
from app.models.service import Service


class ServicesActions(str, Enum):
    show = "show"
    show_service = "show_service"
    purchase = "purchase"


class Services(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="servicss"):
        service_id: int = 0
        action: ServicesActions

    def __init__(self, services: list[Service], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for service in services:
            self.button(
                text=service.display_name,
                callback_data=self.Callback(
                    service_id=service.id, action=ServicesActions.show_service
                ),
            )
        self.adjust(1, 1, 1)


class PurchaseService(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="prchssrv"):
        service_id: int = 0

    def __init__(
        self, service: Service, has_balance: bool = True, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        if has_balance:
            self.button(
                text="🛒 خرید سرویس", callback_data=self.Callback(service_id=service.id)
            )
        else:
            self.button(
                text="💳 افزایش موجودی",
                callback_data=UserPanel.Callback(action=UserPanelAction.charge),
            )
        self.button(
            text="🔙 برگشت", callback_data=Services.Callback(action=ServicesActions.show)
        )
        self.adjust(1, 1)
