import io
from datetime import datetime as dt

import qrcode
from aiogram import F, exceptions
from aiogram.filters import Command, CommandObject
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InputMediaPhoto,
    Message,
    ReplyKeyboardRemove,
)
from tortoise.transactions import in_transaction

from app.keyboards.base import MainMenu
from app.keyboards.user.account import UserPanel, UserPanelAction
from app.keyboards.user.proxy import (
    ConfirmProxyPanel,
    ConfirmRenew,
    Proxies,
    ProxiesActions,
    ProxyLinks,
    ProxyPanel,
    ProxyPanelActions,
    RenewMethods,
    RenewSelectMethod,
    RenewSelectService,
    ResetPassword,
)
from app.marzban import Marzban
from app.models.proxy import Proxy, ProxyStatus
from app.models.service import Service
from app.models.user import Invoice, User
from app.utils import helpers
from app.utils.filters import IsJoinedToChannel, SuperUserAccess
from marzban_client.api.user import (
    get_user_api_user_username_get,
    modify_user_api_user_username_put,
    remove_user_api_user_username_delete,
    reset_user_data_usage_api_user_username_reset_post,
    revoke_user_subscription_api_user_username_revoke_sub_post,
)
from marzban_client.models.user_modify import UserModify
from marzban_client.models.user_modify_inbounds import UserModifyInbounds
from marzban_client.models.user_modify_proxies import UserModifyProxies
from marzban_client.models.user_status import UserStatus

from . import router

PROXY_STATUS = {
    UserStatus.ACTIVE: "فعال ✅",
    UserStatus.DISABLED: "غیرفعال ❌",
    UserStatus.LIMITED: "محدود شده 🔒",
    UserStatus.EXPIRED: "منقضی شده ⏳",
}


class SetCustomNameForm(StatesGroup):
    proxy_id = State()
    user_id = State()
    current_page = State()
    name = State()


class ApiUserError(Exception):
    pass


@router.message(F.text == MainMenu.proxies, IsJoinedToChannel())
@router.callback_query(UserPanel.Callback.filter(F.action == UserPanelAction.proxies))
@router.callback_query(Proxies.Callback.filter(F.action == ProxiesActions.show))
async def proxies(
    qmsg: Message | CallbackQuery,
    user: User,
    callback_data: Proxies.Callback | UserPanel.Callback = None,
):
    if isinstance(callback_data, Proxies.Callback):
        user_id = (
            callback_data.user_id
            if callback_data and callback_data.user_id
            else user.id
        )
        page = callback_data.current_page if callback_data else 0
    else:
        user_id = user.id
        page = 0

    q = Proxy.filter(user_id=user_id).limit(11).offset(0 if page == 0 else page * 10)

    count = await q.count()
    if count < 1:
        text = "در حال حاضر هیچ پروکسی فعالی ندارید😬"
        if isinstance(qmsg, CallbackQuery):
            return qmsg.answer(text, show_alert=True)
        return qmsg.answer(text)

    proxies = await q.prefetch_related("service").all()
    reply_markup = Proxies(
        proxies[:10],
        user_id=user_id,
        current_page=page,
        next_page=True if count > 10 else False,
        prev_page=True if page > 0 else False,
    ).as_markup()
    text = "🔵 لیست پروکسی‌های خریداری شده👇 (برای مدیریت هر پروکسی روی آن کلیک کنید)"
    try:
        if isinstance(qmsg, CallbackQuery):
            return await qmsg.message.edit_text(
                text,
                reply_markup=reply_markup,
            )
        return await qmsg.answer(
            text,
            reply_markup=reply_markup,
        )
    except exceptions.TelegramBadRequest as exc:
        await qmsg.answer("❌ خطایی رخ داد!")
        raise exc


@router.message(F.text == MainMenu.cancel, StateFilter(SetCustomNameForm))
@router.message(Command("proxy"), SuperUserAccess())
@router.callback_query(Proxies.Callback.filter(F.action == ProxiesActions.show_proxy))
async def show_proxy(
    qmsg: Message | CallbackQuery,
    user: User,
    callback_data: Proxies.Callback = None,
    state: FSMContext = None,
    command: CommandObject = None,
):
    if command:
        proxy_id, user_id, current_page = None, None, 0
        proxy = await Proxy.filter(username__iexact=command.args).first()
    else:
        proxy_id, user_id, current_page = None, None, None
        if (state is not None) and (await state.get_state() is not None):
            data = await state.get_data()
            proxy_id, user_id, current_page = data.values()
            text = "🌀 عملیات لغو شد!"
            await state.clear()
            if isinstance(qmsg, CallbackQuery):
                await qmsg.answer(text)
            else:
                await qmsg.answer(text=text, reply_markup=ReplyKeyboardRemove())
        if callback_data:
            proxy_id, user_id, current_page = (
                proxy_id or callback_data.proxy_id,
                user_id or callback_data.user_id,
                current_page or callback_data.current_page,
            )
        proxy = await Proxy.filter(id=proxy_id).first()
    if not proxy:
        return await qmsg.answer("❌ اشتراک مورد نظر یافت نشد!")

    if user_id:
        if (user.role < user.Role.admin) and (user.id != user_id):
            return
        elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
            await proxy.fetch_related("user")
            if proxy.user.parent_id != user.id:
                return
    try:
        client = Marzban.get_server(proxy.server_id)
        sv_proxy = await get_user_api_user_username_get.asyncio(
            username=proxy.username, client=client
        )
    except Exception as err:
        await qmsg.answer(
            f"❌ خطایی در دریافت اطلاعات سرویس رخ داد! لطفا کمی بعد دوباره تلاش کنید."
        )
        raise err
    await proxy.fetch_related("service")
    if not sv_proxy:
        proxy.status = ProxyStatus.disabled
        await proxy.save()
        if user.role < user.Role.admin:
            return await qmsg.answer(
                f"❌ پروکسی مورد نظر در سرور یافت نشد! لطفا با پشتیبانی تماس بگیرید.",
                show_alert=True,
            )
        await proxy.refresh_from_db()
        await proxy.service.fetch_related("server")
        text = f"""
❌ پروکسی در سرور یافت نشد!

آیدی: {proxy.id}
نام تنظیم شده: {proxy.custom_name}
شناسه: {proxy.username}
هزینه: {proxy.cost:,}

سرویس: {proxy.service.display_name}
        """
        await proxy.fetch_related("reserve")
        reply_markup = ProxyPanel(
            proxy,
            user_id=user_id,
            current_page=current_page,
            renewable=False
            if proxy.service.one_time_only
            or proxy.service.is_test_service
            or not proxy.service.renewable
            else True,
        ).as_markup()
        if isinstance(qmsg, CallbackQuery):
            return await qmsg.message.edit_text(text, reply_markup=reply_markup)
        return await qmsg.answer(text, reply_markup=reply_markup)

    if proxy.status.value != sv_proxy.status.value:
        proxy.status = sv_proxy.status.value
        await proxy.save()
        await proxy.refresh_from_db()
    text = f"""
⭐️ شناسه: <code>{sv_proxy.username}</code> {f'({proxy.custom_name})' if proxy.custom_name else ''}
🌀 وضعیت: <b>{PROXY_STATUS.get(sv_proxy.status)}</b>
⏳ تاریخ انقضا: <b>{helpers.hr_date(sv_proxy.expire) if sv_proxy.expire else '♾'}</b> {f'<i>({helpers.hr_time(sv_proxy.expire - dt.now().timestamp(), lang="fa")})</i>' if sv_proxy.expire and sv_proxy.status != UserStatus.EXPIRED else ''}
📊 حجم مصرف شده: <b>{helpers.hr_size(sv_proxy.used_traffic, lang='fa')}</b>
{f'🔋 حجم باقی‌مانده: <b>{helpers.hr_size(sv_proxy.data_limit - sv_proxy.used_traffic ,lang="fa")}</b>' if sv_proxy.data_limit else ''}

🔑 پروکسی های فعال: {', '.join([f'<b>{t.upper()}</b>' for t in [protocol for protocol in sv_proxy.inbounds.additional_properties]])}

🔗 لینک اتصال هوشمند: 
<code>{sv_proxy.subscription_url}</code>

❕برای اطلاع یافتن از وضعیت پروکسی بدون وارد شدن به ربات، میتونید لینک اتصال هوشمند رو ذخیره کنید و در مروگر باز کنید، یا اینکه روی لینک زیر کلیک کنید:
<a href='{sv_proxy.subscription_url}'>🔺 اتصال هوشمند</a>

💡 برای دریافت راهنمای اتصال و استفاده دستور /help را ارسال کنید!
"""
    if sv_proxy.status == UserStatus.ACTIVE:
        text += """

💡 برای قطع اتصال افراد متصل می‌توانید از دکمه «تغییر پسوورد» استفاده کنید!

💡 برای دریافت لینک‌های اتصال و Qr Code میتوانید از دکمه زیر استفاده کنید👇
"""
    reply_markup = ProxyPanel(
        proxy,
        user_id=user_id,
        current_page=current_page,
        renewable=False
        if proxy.service.one_time_only
        or proxy.service.is_test_service
        or not proxy.service.renewable
        else True,
    ).as_markup()
    if isinstance(qmsg, CallbackQuery):
        return await qmsg.message.edit_text(text, reply_markup=reply_markup)
    return await qmsg.answer(text, reply_markup=reply_markup)


@router.callback_query(ProxyPanel.Callback.filter(F.action == ProxyPanelActions.remove))
async def remove_proxy(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    if not callback_data.confirmed:
        return await query.message.edit_text(
            "⚠️ مطمئن هستید که میخواهید سرویس مورد نظر را از لیست پروکسی‌های خود حذف کنید؟ پس از حذف امکان تمدید وجود نخواهد داشت!",
            reply_markup=ConfirmProxyPanel(
                action=ProxyPanelActions.remove,
                proxy_id=callback_data.proxy_id,
                user_id=callback_data.user_id or user.id,
                current_page=callback_data.current_page,
            ).as_markup(),
        )

    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    try:
        client = Marzban.get_server(proxy.server_id)
        sv_proxy = await get_user_api_user_username_get.asyncio(
            username=proxy.username, client=client
        )
    except Exception as err:
        await query.answer(
            f"❌ خطایی در دریافت اطلاعات سرویس رخ داد! لطفا کمی بعد دوباره تلاش کنید."
        )
        raise err

    try:
        if sv_proxy:
            await remove_user_api_user_username_delete.asyncio(
                username=sv_proxy.username, client=client
            )
        await proxy.delete()

        await query.answer("✅ اشتراک از لیست پروکسی‌های شما حذف شد", show_alert=True)
        await proxies(
            query,
            user,
            callback_data=Proxies.Callback(
                user_id=callback_data.user_id,
                action=ProxiesActions.show,
                current_page=callback_data.current_page,
            ),
        )
    except Exception:
        await query.answer(
            "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید."
        )


@router.callback_query(
    ProxyPanel.Callback.filter(F.action == ProxyPanelActions.reset_password)
)
async def reset_password(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    text = """
💡 در این بخش می‌توانید  دسترسی افراد متصل را قطع کنید!

برای انجام این کار دو روش دارید:
1️⃣ تغییر پسوورد: فقط پسوورد کانفیگ‌ها عوض شده و کاربر با استفاده از لینک اتصال هوشمند می‌تواند دوباره متصل شود.
2️⃣ تغییر اتصال هوشمند: لینک اتصال هوشمند کاربر را تغییر می‌دهد و کاربر توانایی آپدیت و استفاده از لینک اتصال هوشمند قدیمی را نخواهد داشت.

اگه میخواید دسترسی کاربر رو به صورت کامل قطع کنید، باید از هر دو روش استفاده کنید🫡
"""
    await query.message.edit_text(
        text,
        reply_markup=ResetPassword(
            proxy_id=callback_data.proxy_id,
            user_id=callback_data.user_id,
            current_page=callback_data.current_page,
        ).as_markup(),
    )


@router.callback_query(
    ProxyPanel.Callback.filter(F.action == ProxyPanelActions.reset_uuid)
)
async def reset_uuid(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    if not callback_data.confirmed:
        return await query.message.edit_text(
            "⚠️ مطمئن هستید که میخواهید پسوورد سرویس مورد نظر تغییر کند؟ تمام افراد متصل قطع خواهند شد!",
            reply_markup=ConfirmProxyPanel(
                action=ProxyPanelActions.reset_uuid,
                proxy_id=callback_data.proxy_id,
                user_id=callback_data.user_id or user.id,
                current_page=callback_data.current_page,
            ).as_markup(),
        )

    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    try:
        client = Marzban.get_server(proxy.server_id)
        sv_proxy = await get_user_api_user_username_get.asyncio(
            username=proxy.username, client=client
        )
    except Exception as err:
        await query.answer(
            f"❌ خطایی در دریافت اطلاعات سرویس رخ داد! لطفا کمی بعد دوباره تلاش کنید."
        )
        raise err
    try:
        await proxy.fetch_related("service")
        sv_proxy = await modify_user_api_user_username_put.asyncio(
            username=sv_proxy.username,
            client=client,
            json_body=UserModify(
                proxies=UserModifyProxies.from_dict(
                    {
                        protocol: proxy.service.create_proxy_protocols(protocol)
                        for protocol in sv_proxy.proxies.additional_properties
                    }
                )
            ),
        )

        await query.answer("✅ پسوورد پروکسی تغییر یافت", show_alert=True)

        await show_proxy(
            query,
            user,
            callback_data=Proxies.Callback(
                proxy_id=proxy.id,
                user_id=user_id,
                action=ProxiesActions.show_proxy,
                current_page=callback_data.current_page,
            ),
        )
    except Exception:
        await query.answer(
            "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید."
        )


@router.callback_query(
    ProxyPanel.Callback.filter(F.action == ProxyPanelActions.reset_subscription)
)
async def reset_subscription(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    if not callback_data.confirmed:
        return await query.message.edit_text(
            "⚠️ مطمئن هستید که میخواهید لینک اتصال هوشمند سرویس مورد نظر تغییر کند؟ امکان استفاده از لینک اتصال هوشمند قدیمی وجود نخواهد داشت!",
            reply_markup=ConfirmProxyPanel(
                action=ProxyPanelActions.reset_subscription,
                proxy_id=callback_data.proxy_id,
                user_id=callback_data.user_id or user.id,
                current_page=callback_data.current_page,
            ).as_markup(),
        )

    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    try:
        client = Marzban.get_server(proxy.server_id)
        sv_proxy = await get_user_api_user_username_get.asyncio(
            username=proxy.username, client=client
        )
    except Exception as err:
        await query.answer(
            f"❌ خطایی در دریافت اطلاعات سرویس رخ داد! لطفا کمی بعد دوباره تلاش کنید."
        )
        raise err
    try:
        await revoke_user_subscription_api_user_username_revoke_sub_post.asyncio(
            username=sv_proxy.username,
            client=client,
        )

        await query.answer("✅ لینک اتصال هوشمند تغییر یافت", show_alert=True)

        await show_proxy(
            query,
            user,
            callback_data=Proxies.Callback(
                proxy_id=proxy.id,
                user_id=user_id,
                action=ProxiesActions.show_proxy,
                current_page=callback_data.current_page,
            ),
        )
    except Exception:
        await query.answer(
            "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید."
        )


@router.callback_query(ProxyPanel.Callback.filter(F.action == ProxyPanelActions.links))
async def proxy_links(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    try:
        client = Marzban.get_server(proxy.server_id)
        sv_proxy = await get_user_api_user_username_get.asyncio(
            username=proxy.username, client=client
        )
    except Exception as err:
        await query.answer(
            "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید.",
            show_alert=True,
        )
        raise err
    if not sv_proxy:
        return await query.answer(
            "❌ خطایی در دریافت اطلاعات سرویس رخ داد! لطفا کمی بعد دوباره تلاش کنید.",
            show_alert=True,
        )
    links = "\n\n".join([f"<code>{link}</code>" for link in sv_proxy.links])
    text = f"""
🔑 پروکسی های فعال: {', '.join(f'<b>{protocol.upper()}</b>' for protocol in sv_proxy.inbounds.additional_properties)}:
    🔗 لینک‌های اتصال:
    
{links}

💡 برای کپی کردن هرکدام از لینک‌ها روی آن کلیک کنید👆

💡 برای دریافت راهنمای اتصال و استفاده دستور /help را ارسال کنید!

📷 برای دریافت <b>Qr code</b> از دکمه‌های زیر استفاده کنید👇
    """
    await query.message.edit_text(
        text,
        reply_markup=ProxyLinks(
            proxy=proxy, current_page=callback_data.current_page, user_id=user_id
        ).as_markup(),
    )


def gen_qr(text: str) -> qrcode.QRCode:
    qr = qrcode.QRCode(border=6)
    qr.add_data(text)
    return qr


async def generate_qr_code(
    message: Message, links: list[str], username: str
) -> BufferedInputFile:
    photos = list()
    for link in links:
        f = io.BytesIO()
        qr = gen_qr(link)
        qr.make_image().save(f)
        f.seek(0)
        photos.append(
            InputMediaPhoto(
                media=BufferedInputFile(
                    f.getvalue(), filename=f"generated_qr_code_{username}"
                ),
                caption=f"{link.split('://')[0].upper()} ({username})",
            )
        )
    return await message.answer_media_group(
        photos,
    )


async def generate_sub_qr_code(message: Message, link: str, username: str):
    f = io.BytesIO()
    qr = gen_qr(link)
    qr.make_image().save(f)
    f.seek(0)
    await message.answer_photo(
        photo=BufferedInputFile(f.getvalue(), filename=f"generated_qr_code_{username}"),
        caption=f"⛓ لینک Qr code اتصال هوشمند ({username})",
    )


@router.callback_query(
    ProxyPanel.Callback.filter(F.action == ProxyPanelActions.links_allqr)
)
async def generate_qrcode_all(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    try:
        client = Marzban.get_server(proxy.server_id)
        sv_proxy = await get_user_api_user_username_get.asyncio(
            username=proxy.username, client=client
        )
    except Exception as err:
        await query.answer(
            "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید.",
            show_alert=True,
        )
        raise err
    if not sv_proxy:
        return await query.answer(
            "❌ خطایی در دریافت اطلاعات سرویس رخ داد! لطفا کمی بعد دوباره تلاش کنید.",
            show_alert=True,
        )

    await query.answer("♻️ درحال ساخت و ارسال Qr code. چند لحظه منتظر بمانید...")

    await generate_qr_code(query.message, sv_proxy.links, username=proxy.username)


@router.callback_query(
    ProxyPanel.Callback.filter(F.action == ProxyPanelActions.links_subqr)
)
async def generate_qrcode_sub(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    try:
        client = Marzban.get_server(proxy.server_id)
        sv_proxy = await get_user_api_user_username_get.asyncio(
            username=proxy.username, client=client
        )
    except Exception as err:
        await query.answer(
            "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید.",
            show_alert=True,
        )
        raise err
    if not sv_proxy:
        return await query.answer(
            "❌ خطایی در دریافت اطلاعات سرویس رخ داد! لطفا کمی بعد دوباره تلاش کنید.",
            show_alert=True,
        )

    await query.answer("♻️ درحال ساخت و ارسال Qr code. چند لحظه منتظر بمانید...")
    await generate_sub_qr_code(
        query.message, sv_proxy.subscription_url, username=proxy.username
    )


@router.callback_query(ProxyPanel.Callback.filter(F.action == ProxyPanelActions.renew))
async def renew_proxy(
    query: CallbackQuery, user: User, callback_data: ProxyPanel.Callback
):
    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    q = Service.filter(
        server_id=proxy.server_id,
        renewable=True,
        one_time_only=False,
        server__is_enabled=True,
        is_test_service=False,
    )
    if user.role == User.Role.reseller:
        q = q.filter(users_only=False)
    elif user.role == User.Role.user:
        q = q.filter(resellers_only=False)

    available_services = await q.all()
    if not available_services:
        text = """
❗️برای اشتراک مورد نظر امکان تمدید وجود ندارد!
لطفا با پشتیبانی تماس بگیرید.
    """
        return await query.answer(text, show_alert=True)

    text = """
♻️ از این بخش میتونید اشتراک خریداری‌شده خودتون رو تمدید کنید!

برای تمدید اشتراک میتونید یکی از سرویس‌های زیر رو انتخاب کنید:
    """
    await query.message.edit_text(
        text,
        reply_markup=RenewSelectService(
            proxy=proxy,
            services=available_services,
            user_id=callback_data.user_id,
            current_page=callback_data.current_page,
        ).as_markup(),
    )


@router.callback_query(RenewSelectService.Callback.filter())
async def renew_proxy_service(
    query: CallbackQuery, user: User, callback_data: RenewSelectService.Callback
):
    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    text = """
✅ برای تمدید میتونید یکی از حالت‌های زیر رو انتخاب کنید👇

➖ تمدید آنی: دوره جدید اشتراک شما از همین لحظه محاسبه می‌شود و سرویس جدید برای شما فعال می‌شود.

➖ رزور پلن پشتیبان: پس از اتمام حجم یا دوره اشتراک فعلی، سرویس جدید به طور خودکار فعال می‌شود.

یکی از حالت‌های تمدید رو انتخاب کنید👇
    """
    await query.message.edit_text(
        text,
        reply_markup=RenewSelectMethod(
            proxy=proxy,
            service_id=callback_data.service_id,
            user_id=callback_data.user_id,
            current_page=callback_data.current_page,
        ).as_markup(),
    )


@router.callback_query(RenewSelectMethod.Callback.filter(F.method == RenewMethods.now))
async def renew_proxy_now(
    query: CallbackQuery, user: User, callback_data: RenewSelectMethod.Callback
):
    user_id = callback_data.user_id if callback_data.user_id else user.id
    proxy = await Proxy.filter(id=callback_data.proxy_id).first()
    if (user.role < user.Role.admin) and (user.id != user_id):
        return
    elif (user.role == user.Role.admin) and (proxy.user_id != user_id):
        await proxy.fetch_related("user")
        if proxy.user.parent_id != user.id:
            return

    service = await Service.filter(
        id=callback_data.service_id,
        renewable=True,
        server__is_enabled=True,
        is_test_service=False,
    ).first()
    if not service:
        return await query.answer(
            "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید.",
            show_alert=True,
        )

    price = service.get_price()
    await user.fetch_related("setting")
    if user.setting and (discount_percentage := user.setting.discount_percentage):
        discounted_price = service.get_price(discount_percent=discount_percentage)
    else:
        discounted_price = price

    balance = await user.get_available_credit()

    if callback_data.confirmed:
        if balance < discounted_price:
            return await query.answer(
                "❌ موجودی حساب شما کافی نمی‌باشد!", show_alert=True
            )
        try:
            async with in_transaction():
                await Invoice.create(
                    amount=discounted_price,
                    type=Invoice.Type.renew_now,
                    is_paid=not user.is_postpaid,
                    proxy=proxy,
                    user=user,
                )
                client = Marzban.get_server(service.server_id)
                updated_user = UserModify(
                    expire=helpers.get_expire_timestamp(service.expire_duration),
                    data_limit=service.data_limit,
                )
                sv_proxy = (
                    await reset_user_data_usage_api_user_username_reset_post.asyncio(
                        username=proxy.username, client=client
                    )
                )
                if not sv_proxy:
                    raise ApiUserError("reset data usage didn't return anything!")
                updated_user = UserModify(
                    expire=helpers.get_expire_timestamp(service.expire_duration),
                    data_limit=service.data_limit,
                )
                if service.id != proxy.service_id:
                    proxy.service_id = service.id
                    updated_user.inbounds = UserModifyInbounds.from_dict(
                        service.inbounds
                    )
                    proxies = {}
                    for protocol in service.inbounds:
                        if protocol in sv_proxy.proxies:
                            proxies.update({protocol: sv_proxy.proxies.get(protocol)})
                        else:
                            proxies.update(
                                {protocol: service.create_proxy_protocols(protocol)}
                            )
                    updated_user.proxies = UserModifyProxies.from_dict(proxies)
                sv_proxy = await modify_user_api_user_username_put.asyncio(
                    username=proxy.username,
                    json_body=updated_user,
                    client=client,
                )
                proxy.status = sv_proxy.status.value
                await proxy.save()
                if not sv_proxy:
                    raise ApiUserError("modify user didn't return anything!")
                await query.answer("✅ سرویس شما با موفقیت تمدید شد!", show_alert=True)
                return await show_proxy(
                    query,
                    user,
                    callback_data=Proxies.Callback(
                        proxy_id=proxy.id,
                        user_id=callback_data.user_id,
                        action=ProxiesActions.show_proxy,
                        current_page=callback_data.current_page,
                    ),
                )
        except Exception as err:
            await query.answer(
                "❌ خطایی در انجام عملیات رخ داد! لطفا با پشتیبانی تماس بگیرید.",
                show_alert=True,
            )
            raise err

    text = f"""
🌀 آیا مایل به فعال سازی سرویس زیر برای این پروکسی هستید؟

💎 {service.name}
🕐 مدت زمان: {helpers.hr_time(service.expire_duration, lang="fa") if service.expire_duration else '♾'}
🖥 حجم: {helpers.hr_size(service.data_limit, lang="fa") if service.data_limit else '♾'}
💰 قیمت: {price:,} تومان
"""
    if discounted_price < price:
        text += f"""
~~~~~~~~~~~~~~~~~~~~~~~~
🔥 تخفیف ویژه شما: <code>{discount_percentage}</code> درصد
💰 قیمت با تخفیف: <code>{discounted_price:,}</code> تومان
~~~~~~~~~~~~~~~~~~~~~~~~
"""
    text += f"""
🏦 موجودی حساب شما: {balance:,} تومان
💵 مبلغ قابل پرداخت: {discounted_price:,} تومان
~~~~~~~~~~~~~~~~~~~~~~~~
    """
    if balance >= discounted_price:
        text += "🛍 برای تمدید آنی و فعالسازی سرویس، دکمه زیر را کلیک کنید👇"
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmRenew(
                proxy=proxy,
                service_id=service.id,
                method=RenewMethods.now,
                user_id=callback_data.user_id,
                current_page=callback_data.current_page,
            ).as_markup(),
        )
    text += "😞 موجودی حساب شما برای فعالسازی این سرویس کافی نیست! برای افزایش اعتبار دکمه زیر را کلیک کنید👇"
    return await query.message.edit_text(
        text,
        reply_markup=ConfirmRenew(
            proxy=proxy,
            service_id=service.id,
            method=RenewMethods.now,
            user_id=callback_data.user_id,
            current_page=callback_data.current_page,
            has_balance=False,
        ).as_markup(),
    )
