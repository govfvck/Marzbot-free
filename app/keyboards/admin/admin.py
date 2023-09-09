from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class AdminPanelAction(str, Enum):
    servers = "servers"
    services = "services"
    users = "users"
    panel = "panel"
    settings = "settings"


class AdminPanel(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="admin"):
        action: AdminPanelAction

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text="Servers", callback_data=self.Callback(action=AdminPanelAction.servers)
        )
        self.button(
            text="Services",
            callback_data=self.Callback(action=AdminPanelAction.services),
        )
        self.button(
            text="Users", callback_data=self.Callback(action=AdminPanelAction.users)
        )
        self.button(
            text="Settings",
            callback_data=self.Callback(action=AdminPanelAction.settings),
        )
        self.adjust(2, 1, 1)


class CancelFormAdmin(ReplyKeyboardBuilder):
    cancel = "cancel"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(text=self.cancel)


class YesOrNoFormAdmin(ReplyKeyboardBuilder):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(text="Yes")
        self.button(text="No")
        self.button(text=CancelFormAdmin.cancel)
        self.adjust(2, 1)
