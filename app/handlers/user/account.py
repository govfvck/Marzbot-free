from aiogram import F
from aiogram.types import CallbackQuery, Message

from app.keyboards.base import MainMenu
from app.keyboards.user.account import UserPanel, UserPanelAction
from app.models.user import User
from app.utils.filters import IsJoinedToChannel

from . import router

ACCOUNT_TYPE = {
    "user": "کاربر معمولی",
    "reseller": "فروشنده",
    "admin": "ادمین",
    "super_user": "ادمین اصلی",
}


@router.message(F.text == MainMenu.account, IsJoinedToChannel())
@router.callback_query(UserPanel.Callback.filter(F.action == UserPanelAction.show))
async def account(qmsg: Message | CallbackQuery, user: User):
    balance = await user.get_balance()
    text = f"""
✅ اطلاعات حساب شما:

💬 نام کاربری: {f'@{user.username}' if user.username else '➖'}
📲 شناسه کاربری: <code>{user.id}</code>
💲 اعتبار در دسترس: <b>{balance:,}</b> تومان
🔋 سرویس‌های فعال: <b>{await user.proxies.all().count()}</b>
~~~~~~~~~~~~~~~~~~~~~~~~
👤 نوع اکانت: {ACCOUNT_TYPE.get(user.role.name)}"""

    if isinstance(qmsg, CallbackQuery):
        return await qmsg.message.edit_text(
            text + "‌‌",
            reply_markup=UserPanel(user=user).as_markup(),
        )
    await qmsg.answer(text + "‌‌", reply_markup=UserPanel(user=user).as_markup())
