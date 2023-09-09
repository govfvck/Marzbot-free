from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
from app.keyboards.base import ForceJoin, MainMenu
from app.models.user import User
from app.utils import helpers
from app.utils.filters import IsJoinedToChannel

from .start import main_menu_handler

router = Router(name="base")


@router.message((F.text == MainMenu.cancel) | (F.text == MainMenu.back))
@router.message(Command(commands=["cancel"]))
async def cancel_handler(message: Message, user: User, state: FSMContext):
    """
    Allow user to cancel any action
    """
    await main_menu_handler(message, user)


@router.message(F.text == MainMenu.support)
async def support(message: Message, user: User):
    await message.answer(config.SUPPORT_TEXT, disable_web_page_preview=True)


@router.message(Command("help"))
@router.message(F.text == MainMenu.help)
async def shelp(message: Message, user: User):
    await message.answer(config.HELP_TEXT, disable_web_page_preview=True)


@router.callback_query(ForceJoin.Callback.filter())
async def check_force_join(query: CallbackQuery, user: User):
    if await helpers.check_force_join(user):
        await query.message.edit_text("✅ عضویت شما در کانال تایید شد")
        return await main_menu_handler(
            query,
            user,
        )
    await query.answer("🚫 عضویت شما در کانال تایید نشد!", show_alert=True)


@router.message(~IsJoinedToChannel(send_alert=False))
async def force_join_ph(message: Message):
    return


@router.message()
async def command_not_found(message: Message):
    text = """
🤕 متوجه دستور ارسالی نشدم!
برای رفتن به منوی اصلی دستور /menu رو ارسال کنید😉
    """
    await message.reply(text)
