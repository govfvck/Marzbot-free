from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.user import User

from ..user import proxy
from .admin import AdminPanel, AdminPanelAction


class Users(InlineKeyboardBuilder):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text="Back",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.panel),
        )
        self.adjust(1, 1)


class ManageUserAction(str, Enum):
    discount_percent = "discount_percent"


class ManageUser(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="admmngusr"):
        user_id: int
        action: ManageUserAction

    def __init__(
        self,
        user: User,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text=f"پروکسی‌ها",
            callback_data=proxy.Proxies.Callback(
                user_id=user.id,
                action=proxy.ProxiesActions.show,
                current_page=0,
            ),
        )
        self.adjust(1, 1)
