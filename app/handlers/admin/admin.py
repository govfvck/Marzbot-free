import asyncio

from aiogram import F, exceptions
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.admin.admin import AdminPanel, AdminPanelAction
from app.main import bot
from app.models.user import User
from app.utils.filters import SuperUserAccess

from . import logger, router


@router.message(Command("admin"), SuperUserAccess())
@router.callback_query(
    AdminPanel.Callback.filter(F.action == AdminPanelAction.panel), SuperUserAccess()
)
async def show_admin_panel(
    message: Message | CallbackQuery, user: User, state: FSMContext = None
):
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()

    text = "admin panel:"
    if isinstance(message, CallbackQuery):
        return await message.message.edit_text(
            text,
            reply_markup=AdminPanel().as_markup(),
        )
    return await message.answer(
        text,
        reply_markup=AdminPanel().as_markup(),
    )


# send message
@router.message(Command("msg"), SuperUserAccess())
async def msg_command(message: Message, user: User):
    """send message to a user
    Args:
        user (int | str): user id or username of the user
        text (str): text to be sent to the user

    Example:
        /msg @test hello
    """
    user_id = message.text.split()[1]
    text = " ".join(message.text.split()[2:])

    if user_id.isnumeric():
        user_to_get = await User.filter(id=int(user_id)).first()
    else:
        user_to_get = await User.filter(username__iexact=user_id.lstrip("@")).first()

    if not user_to_get:
        return await message.answer(f"User {user_id} not found!")

    try:
        msg_text = f"""
🔔 شما یک پیام از طرف پشتیبانی دارید:
~~~~~~~~~~~~~~~~~~~~~~~~
{text}
‌‌
"""
        await bot.send_message(chat_id=user.id, text=msg_text)
        return await message.reply(
            f"message sent to <a href='tg://user?id={user_to_get.id}'>{user_to_get.id}</a>\n\n{msg_text}"
        )
    except Exception as exc:
        await message.reply(f"Error:\n{exc}")
        raise exc


# Broadcast messages
async def fwd_msg(message: Message, user: User):
    try:
        await message.forward(user.id)
    except exceptions.TelegramRetryAfter as err:
        await asyncio.sleep(err.retry_after)
        return await fwd_msg(message, user)
    except exceptions.TelegramAPIError:
        return False
    except Exception as err:
        logger.error(f"Unknown error in fwd_msg: {err}")
        return False
    return True


async def send_msg(message: Message, user: User):
    try:
        await bot(message.send_copy(user.id))
    except exceptions.TelegramRetryAfter as err:
        await asyncio.sleep(err.retry_after)
        return await send_msg(message, user)
    except exceptions.TelegramAPIError:
        return False
    except Exception as err:
        logger.error(f"Unknown error in send_msg: {err}")
        return False
    return True


async def broadcast(message: Message, sender: callable, type: str):
    if not message.reply_to_message:
        return await message.reply(f"برای {type} باید روی یک پیام ریپلای کنید!")

    success = 0
    fails = 0
    waiter = 0.1

    users = await User.filter(is_blocked=False).all()
    total = len(users)

    progres = await message.reply(
        f"{type} پیام به {total} کاربر...\n" f"زمان تقریبی: {int((waiter*total)/60)}"
    )

    for idx, user in enumerate(users):
        if await sender(message.reply_to_message, user):
            success += 1
        else:
            fails += 1
        if idx and (idx % 250) == 0:
            await progres.edit_text(
                f"{type} پیام به {total} کاربر...\n" f"پیشرفت: {int(idx/total*100)}%"
            )
        await asyncio.sleep(0.1)
    await progres.edit_text(f"{type} پیام به {total} کاربر...\n" f"پیشرفت: 100%")
    return await message.reply(f"پیام {type} شد!\nموفق: {success}\n ناموفق: {fails}")


@router.message(Command("forward"), SuperUserAccess())
async def forward_command(message: Message, user: User):
    """forwards a message to all users

    Example:
        /forward (reply)
    """
    asyncio.create_task(broadcast(message, fwd_msg, "فوروارد"))


@router.message(Command("broadcast"), SuperUserAccess())
async def broadcast_command(message: Message, user: User):
    """sends a message to all users

    Example:
        /broadcast (reply)
    """
    asyncio.create_task(broadcast(message, send_msg, "ارسال"))
