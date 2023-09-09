from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
from app.keyboards.base import MainMenu
from app.main import bot
from app.models.user import User
from app.utils.settings import Settings

router = Router(name="start")


@router.message(CommandStart(deep_link=False, ignore_case=True))
async def start_handler(message: Message, user: User, command: CommandObject):
    await message.answer(config.START_TEXT)
    await main_menu_handler(message, user)


@router.message(F.text == MainMenu.main_menu)
@router.message(Command(commands="menu"))
async def main_menu_handler(
    qmsg: Message | CallbackQuery, user: User, state: FSMContext = None
):
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
    text = """
♻️ منوی اصلی ربات:
🤖 چه کاری میتونم براتون انجام بدم؟👇
    """
    if isinstance(qmsg, CallbackQuery):
        return await qmsg.message.answer(
            text,
            reply_markup=MainMenu().as_markup(resize_keyboard=True),
        )
    return await qmsg.answer(
        text,
        reply_markup=MainMenu().as_markup(resize_keyboard=True),
    )
