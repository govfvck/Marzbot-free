import inspect
import sys

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from tortoise.transactions import in_transaction

import config
from app.keyboards.admin.admin import AdminPanel, AdminPanelAction
from app.keyboards.admin.user import ManageUser, ManageUserAction, Users
from app.keyboards.base import CancelUserForm
from app.main import bot
from app.models.proxy import Proxy
from app.models.user import ByAdminPayment, Invoice, Transaction, User
from app.utils.filters import SuperUserAccess
from app.utils.settings import Settings

from . import router


class ManageUserForm(StatesGroup):
    user_id = State()
    amount = State()
    discount_percent = State()
    daily_test_services = State()
    proxy_prefix = State()


@router.callback_query(
    AdminPanel.Callback.filter(F.action == AdminPanelAction.users), SuperUserAccess()
)
async def show_users(
    query: CallbackQuery | Message, user: User, state: FSMContext | None = None
):
    text = f"""
User info: <code>/info [user_id]</code>
User Charge: <code>/charge [user_id] [amount]</code>
User Decharge: <code>/decharge [user_id] [amount]</code>
User Block: <code>/block [user_id]</code>
User Unblock: <code>/unblock [user_id]</code>

user commands: /usercmd
"""
    return await query.message.edit_text(text, reply_markup=Users().as_markup())


# get user info
@router.message(Command("info"), SuperUserAccess())
async def get_user_info_command(message: Message, user: User):
    """Get info of a user

    Args:
        user (int | str): user id or username of the user

    Example:
        <code>/info @username</code>
        <code>/info 123456789</code>
    """
    try:
        _, user_id = message.text.split()
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /info [user_id|username]"
        )
    if user_id.isnumeric():
        user_to_get = (
            await User.filter(id=int(user_id)).prefetch_related("setting").first()
        )
    else:
        user_to_get = (
            await User.filter(username__iexact=user_id.lstrip("@"))
            .prefetch_related("setting")
            .first()
        )

    if not user_to_get:
        return await message.answer(f"User {user_id} not found!")

    proxy_count = await Proxy.filter(user_id=user_to_get.id).count()
    balance = await user_to_get.get_balance()
    credit = await user_to_get.get_available_credit(balance=balance)

    text = f"""
id: <code>{user_to_get.id}</code>
username: <b>@{user_to_get.username}</b>
name: <b>{user_to_get.name}</b>
balance: <b>{balance}</b>
available credit: <b>{credit}</b>
is blocked: <b>{user_to_get.is_blocked}</b>
role: <b>{user_to_get.role.name}</b>
proxy counts: <b>{proxy_count}</b>
post paid / max credit: {'Yes' if user_to_get.is_postpaid else 'No'} / {user_to_get.max_post_paid_credit if user_to_get.is_postpaid else 0:,}

total spent: <b>{user_to_get.total_spent:,}</b>

referrer: <code>{user_to_get.referrer_id if user_to_get.referrer_id else '-'}</code>
referred count: <b>{await user_to_get.referred.all().count()}</b>

commands:
    <code>/block {user_to_get.id}</code> <b>Block user</b>
    <code>/unblock {user_to_get.id}</code> <b>Unblock User</b>
    <code>/charge {user_to_get.id}</code> <i>[amount]</i> <b>Create Transaction</b>
    <code>/decharge {user_to_get.id}</code> <i>[amount]</i> <b>Create Invoice</b>
"""
    await message.answer(text, reply_markup=ManageUser(user=user_to_get).as_markup())


@router.message(Command("role"), SuperUserAccess())
async def user_role_command(message: Message, user: User):
    """Change user role

    Args:
        user (int | str): user id or username of the user
        role (str): role of user, [user|reseller|admin|super_user]

    Example:
        <code>/role @username admin</code>
        <code>/role 123456789 admin</code>
    """
    try:
        _, user_id, role = message.text.split()
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /role [user_id|username] [role]"
        )
    if user_id.isnumeric():
        user_to_get = await User.filter(id=int(user_id)).first()
    else:
        user_to_get = await User.filter(username__iexact=user_id.lstrip("@")).first()

    if not user_to_get:
        return await message.answer(f"User {user_id} not found!")

    roles = {"user": 0, "reseller": 1, "admin": 2, "super_user": 3}
    if not role in roles:
        return await message.answer(f"Unknown role! must be one of " + "".join(roles))

    user_to_get.role = roles.get(role)
    await user_to_get.save()
    await user_to_get.refresh_from_db()
    text = f"""
Done!

User id: <code>{user_to_get.id}</code>
Role: <code>{user_to_get.role.name}</code>

Actions:

User info: <code>/info {user_id}</code>
"""
    await message.answer(text)


# charge and decharge user
@router.message(Command("charge"), SuperUserAccess())
async def charge_user_command(message: Message, user: User):
    """Charge user

    Args:
        user (int | str): user id or username of the user
        amount (int): amount

    Example:
        <code>/charge @username 500000</code>
        <code>/charge 123456789 500000</code>
    """
    try:
        _, user_id, amount = message.text.split()
        amount = int(amount)
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /charge [user_id|username] [amount]"
        )
    if user_id.isnumeric():
        user_to_get = await User.filter(id=int(user_id)).first()
    else:
        user_to_get = await User.filter(username__iexact=user_id.lstrip("@")).first()

    if not user_to_get:
        return await message.answer(f"User {user_id} not found!")

    async with in_transaction():
        transaction = await Transaction.create(
            type=Transaction.PaymentType.by_admin,
            status=Transaction.Status.finished,
            amount=amount,
            user=user_to_get,
        )
        await ByAdminPayment.create(
            by_admin=user,
            transaction=transaction,
        )
    text = f"""
Done!

Transaction id: <code>{transaction.id}</code>
Amount: <code>{transaction.amount:,}</code>
User id: <code>{transaction.user_id}</code>

Actions:

Undo: <code>/undotr {transaction.id}</code>
User info: <code>/info {transaction.user_id}</code>
"""
    await message.answer(text)
    await bot.send_message(
        user_to_get.id,
        f"✅ مبلغ {transaction.amount:,} تومان از طرف <code>{user.id}</code> به حساب شما اضافه شد!",
    )


@router.message(Command("decharge"), SuperUserAccess())
async def decharge_user_command(message: Message, user: User):
    """DeCharge user

    Args:
        user (int | str): user id or username of the user
        amount (int): amount

    Example:
        <code>/decharge @username 500000</code>
        <code>/decharge 123456789 500000</code>
    """
    try:
        _, user_id, amount = message.text.split()
        amount = int(amount)
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /decharge [user_id|username] [amount]"
        )
    if user_id.isnumeric():
        user_to_get = await User.filter(id=int(user_id)).first()
    else:
        user_to_get = await User.filter(username__iexact=user_id.lstrip("@")).first()

    if not user_to_get:
        return await message.answer(f"User {user_id} not found!")

    invoice = await Invoice.create(
        amount=amount,
        type=Invoice.Type.by_admin,
        user=user_to_get,
    )
    text = f"""
Done!

Invoice id: <code>{invoice.id}</code>
Amount: <code>{invoice.amount:,}</code>
User id: <code>{invoice.user_id}</code>

Actions:

Undo: <code>/undoiv {invoice.id}</code>
User info: <code>/info {invoice.user_id}</code>
"""
    await message.answer(text)


@router.message(Command("undotr"), SuperUserAccess())
async def undotr_command(message: Message, user: User):
    """Remove Transaction

    Args:
        id (int): transaction id

    Example:
        <code>/undotr 112233 </code>
    """
    try:
        _, transaction_id = message.text.split()
        transaction_id = int(transaction_id)
    except ValueError:
        return await message.answer("Could not parse the command! format: /undotr [id]")
    transaction = await Transaction.filter(id=transaction_id).first()

    if not transaction:
        return await message.answer(f"Transaction {transaction_id} not found!")

    await transaction.delete()
    text = f"""
Done!

Transaction id: <code>{transaction.id}</code>
Type: <code>{transaction.type.name}</code>
Amount: <code>{transaction.amount:,}</code>
User id: <code>{transaction.user_id}</code>
"""
    await message.answer(text)


@router.message(Command("undoiv"), SuperUserAccess())
async def undoiv_command(message: Message, user: User):
    """Remove Invoice

    Args:
        id (int): invoice id

    Example:
        <code>/undoiv 112233 </code>
    """
    try:
        _, invoice_id = message.text.split()
        invoice_id = int(invoice_id)
    except ValueError:
        return await message.answer("Could not parse the command! format: /undotr [id]")
    invoice = await Invoice.filter(id=invoice_id).first()

    if not invoice:
        return await message.answer(f"invoice {invoice_id} not found!")

    await invoice.delete()
    text = f"""
Done!

Invoice id: <code>{invoice.id}</code>
Type: <code>{invoice.type.name}</code>
Amount: <code>{invoice.amount:,}</code>
User id: <code>{invoice.user_id}</code>
"""
    await message.answer(text)


# block and unblock users
@router.message(Command("block"), SuperUserAccess())
async def block_user_command(message: Message, user: User):
    """Block user

    Args:
        user (int | str): user id or username of the user

    Example:
        <code>/block @username</code>
        <code>/block 123456789</code>
    """
    try:
        _, user_id = message.text.split()
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /block [user_id|username]"
        )
    if user_id.isnumeric():
        user_to_get = await User.filter(id=int(user_id)).first()
    else:
        user_to_get = await User.filter(username__iexact=user_id.lstrip("@")).first()

    if not user_to_get:
        return await message.answer(f"User {user_id} not found!")

    if (user_to_get.role == User.Role.super_user) or (user_to_get.id == user.id):
        return await message.answer("You cant do that!")

    if user_to_get.is_blocked:
        return await message.answer("User already blocked")

    user_to_get.is_blocked = True
    await user_to_get.save()
    await message.answer(
        f"User <a href='tg://user?id={user_to_get.id}'>{user_to_get.id}</a> blocked!"
    )


@router.message(Command("unblock"), SuperUserAccess())
async def unblock_user_command(message: Message, user: User):
    """Unblock user

    Args:
        user (int | str): user id or username of the user

    Example:
        <code>/unblock @username</code>
        <code>/unblock 123456789</code>
    """
    try:
        _, user_id = message.text.split()
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /unblock [user_id|username]"
        )
    if user_id.isnumeric():
        user_to_get = await User.filter(id=int(user_id)).first()
    else:
        user_to_get = await User.filter(username__iexact=user_id.lstrip("@")).first()

    if not user_to_get:
        return await message.answer(f"User {user_id} not found!")

    if not user_to_get.is_blocked:
        return await message.answer("User is not blocked")

    user_to_get.is_blocked = False
    await user_to_get.save()
    await message.answer(
        f"User <a href='tg://user?id={user_to_get.id}'>{user_to_get.id}</a> unblocked!"
    )


@router.message(Command("access"), SuperUserAccess())
async def access_user_command(message: Message, user: User):
    """Access user

    Args:
        user (int | str): user id of the user

    Example:
        <code>/access 123456789</code>
    """
    try:
        _, user_id = message.text.split()
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /access [user_id]"
        )
    if user_id.isnumeric():
        user_id = int(user_id)
    else:
        return await message.reply("user_id must be numeric!")

    await Settings.give_user_access(user_id)

    await message.answer(
        f"User <a href='tg://user?id={user_id}'>{user_id}</a> has been given access!"
    )


@router.message(Command("noaccess"), SuperUserAccess())
async def noaccess_user_command(message: Message, user: User):
    """Remove user access

    Args:
        user (int | str): user id of the user

    Example:
        <code>/noaccess 123456789</code>
    """
    try:
        _, user_id = message.text.split()
    except ValueError:
        return await message.answer(
            "Could not parse the command! format: /noaccess [user_id]"
        )
    if user_id.isnumeric():
        user_id = int(user_id)
    else:
        return await message.reply("user_id must be numeric!")

    await Settings.remove_user_access(user_id)

    await message.answer(
        f"User <a href='tg://user?id={user_id}'>{user_id}</a> access removed! "
        f"if user already started the bot, you have to block them! try: <code>/info {user_id}</code>"
    )


@router.callback_query(
    ManageUser.Callback.filter(),
    SuperUserAccess(),
)
async def manage_user_action(
    query: CallbackQuery,
    user: User,
    callback_data: ManageUser.Callback,
    state: FSMContext,
):
    managed_user = await User.filter(
        id=callback_data.user_id,
    ).first()
    if not managed_user:
        return await query.answer(f"❌ کاربر یافت نشد!")

    if callback_data.action == ManageUserAction.discount_percent:
        await user.fetch_related("setting")
        if user.role != User.Role.super_user:
            max_discount = user.setting.discount_percentage if user.setting else 0
            if not max_discount:
                return await query.answer(
                    "درصد تخفیف شما تنظیم نشده است، بنابراین امکان تنظیم برای کاربران خود را ندارید! لطفا با پشتیبانی تماس بگیرید.",
                    show_alert=True,
                )
        else:
            max_discount = 100
        text = f"""
درصد تخفیف جدید کاربر را وارد کنید:
(حداکثر {max_discount} درصد)
    """
        await state.set_state(ManageUserForm.discount_percent)

    elif callback_data.action == ManageUserAction.max_test_services:
        await user.fetch_related("setting")
        if user.role != User.Role.super_user:
            max_count = user.setting.daily_test_services if user.setting else 0
            if not max_count or max_count <= 1:
                return await query.answer(
                    "تعداد سرویس‌های تست شما تنظیم نشده است، بنابراین امکان تنظیم برای کاربران خود را ندارید! لطفا با پشتیبانی تماس بگیرید.",
                    show_alert=True,
                )
        else:
            max_count = "+inf"
        text = f"""
تعداد سرویس‌های تست که این کاربر در یک روز می‌تواند دریافت کند را وارد کنید:
(حداکثر {max_count})
    """
        await state.set_state(ManageUserForm.daily_test_services)

    elif callback_data.action == ManageUserAction.proxy_prefix:
        text = f"""
💡 این متن در ابتدای نام پروکسی‌های شما قرار می‌گیرد و فقط میتواند شامل حروف انگلیسی یا اعداد باشد!

💡 مقدار پیشفرض برای پروکسی‌ها <code>{config.DEFAULT_USERNAME_PREFIX}</code> می‌باشد

✍️ پیشوند پروکسی را برای تنظیم وارد کنید:
"""
        await state.set_state(ManageUserForm.proxy_prefix)
    else:
        return

    await state.set_data(
        {
            "user_id": managed_user.id,
        }
    )
    await query.message.delete()
    await query.message.answer(
        text,
        reply_markup=CancelUserForm(cancel=True).as_markup(
            one_time_keyboard=True, resize_keybaord=True
        ),
    )


@router.message(ManageUserForm.discount_percent, SuperUserAccess())
async def manage_users_discount_percent(
    message: Message, user: User, state: FSMContext
):
    try:
        amount = int(message.text)
    except ValueError:
        return await message.reply(
            f"درصد باید مقداری عددی باشد! لطفا دوباره ارسال کنید:"
        )
    if user.role != User.Role.super_user:
        max_discount = user.setting.discount_percentage if user.setting else 0
    else:
        max_discount = 100
    if amount > max_discount:
        return await message.reply(
            f"درصد باید مقداری کمتر از {max_discount} باشد! دوباره ارسال کنید:"
        )

    data = await state.get_data()
    q = UserSetting.filter(user_id=data.get("user_id"))
    if not await q.first():
        await UserSetting.create(
            user_id=data.get("user_id"), discount_percentage=amount
        )
    else:
        await q.update(discount_percentage=amount)

    await state.clear()
    await message.reply(f"درصد تخفیف کاربر به {amount} تنظیم شد!")


@router.message(ManageUserForm.daily_test_services, SuperUserAccess())
async def manage_users_daily_test_services(
    message: Message, user: User, state: FSMContext
):
    try:
        amount = int(message.text)
    except ValueError:
        return await message.reply(
            f"تعداد باید مقداری عددی باشد! لطفا دوباره ارسال کنید:"
        )
    if user.role != User.Role.super_user:
        max_count = user.setting.daily_test_services if user.setting else 0
        if amount > max_count:
            return await message.reply(
                f"تعداد باید مقداری کمتر از {max_count} باشد! دوباره ارسال کنید:"
            )

    data = await state.get_data()
    q = UserSetting.filter(user_id=data.get("user_id"))
    if not await q.first():
        await UserSetting.create(
            user_id=data.get("user_id"), daily_test_services=amount
        )
    else:
        await q.update(daily_test_services=amount)

    await state.clear()
    await message.reply(f"تعداد سرویس‌های تست روزانه کاربر به {amount} تنظیم شد!")


@router.message(ManageUserForm.proxy_prefix, SuperUserAccess())
async def manage_users_daily_test_services(
    message: Message, user: User, state: FSMContext
):
    username_prefix = message.text
    if not username_prefix.isalnum():
        return await message.answer(
            f"❌ پیشوند پروکسی‌ها فقط می‌تواند شامل اعداد و حروف انگلیسی باشد! دوباره ارسال کنید:",
            reply_markup=CancelUserForm(cancel=True).as_markup(
                one_time_keyboard=True, resize_keyboard=True
            ),
        )
    if not (3 < len(username_prefix) < 20):
        return await message.answer(
            f"❌ پیشوند پروکسی‌ها فقط می‌تواند بین ۴ تا ۲۰ کاراکتر باشد! دوباره ارسال کنید:",
            reply_markup=CancelUserForm(cancel=True).as_markup(
                one_time_keyboard=True, resize_keyboard=True
            ),
        )

    data = await state.get_data()
    q = UserSetting.filter(user_id=data.get("user_id"))
    if not await q.first():
        await UserSetting.create(
            user_id=data.get("user_id"), proxy_username_prefix=username_prefix
        )
    else:
        await q.update(proxy_username_prefix=username_prefix)

    await state.clear()
    await message.reply(
        f"پیشوند پروکسی‌های کاربر به <code>{username_prefix}</code> تنظیم شد!"
    )


def generate_commands_help() -> list[str]:
    def sort_by_line(obj: callable):
        return obj.__code__.co_firstlineno

    cmd_functions: list[callable] = [
        obj
        for name, obj in inspect.getmembers(sys.modules[__name__])
        if (
            inspect.isfunction(obj)
            and name.endswith("_command")
            and obj.__doc__ is not None
        )
    ]
    cmd_functions.sort(key=sort_by_line)
    spacer = f"\n{'*' * 30}\n"
    output = list()
    index = 0
    for obj in cmd_functions:
        try:
            if len(output[index]) >= 3500:
                index += 1
                output.insert(index, "")
        except IndexError:
            output.insert(0, "")

        output[index] += spacer
        output[index] += obj.__doc__

    return output


HELP_TEXT = generate_commands_help()


@router.message(Command("usercmd"), SuperUserAccess())
async def show_help_command(message: Message, user: User):
    """Show help message

    /usercmd

    Returns:
        Message: message of help text

    Example:
        /usercmd
    """
    for text in HELP_TEXT:
        await message.reply(text)
