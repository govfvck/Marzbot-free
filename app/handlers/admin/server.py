from aiogram import F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.keyboards.admin.admin import (
    AdminPanel,
    AdminPanelAction,
    CancelFormAdmin,
    YesOrNoFormAdmin,
)
from app.keyboards.admin.server import (
    ConfirmServerAction,
    EditServer,
    EditServerAction,
    ServerAct,
    ServerActAction,
    Servers,
    ServersAction,
)
from app.marzban import Marzban
from app.models.server import Server
from app.models.user import User
from app.utils.filters import SuperUserAccess
from marzban_client import AuthenticatedClient
from marzban_client.api.user import get_users_api_users_get

from . import router

cancel_form = CancelFormAdmin().as_markup(resize_keyboard=True, one_time_only=True)
yes_or_no_form = YesOrNoFormAdmin().as_markup(
    resize_keyboard=True, one_time_keyboard=True
)


class AddServerForm(StatesGroup):
    name = State()
    host = State()
    port = State()
    token = State()
    https = State()
    confirm = State()


class EditServerForm(StatesGroup):
    id = State()
    name = State()
    host = State()
    port = State()
    token = State()
    https = State()


@router.message(
    F.text.casefold() == "cancel", SuperUserAccess(), StateFilter(AddServerForm)
)
@router.message(Command("cancel"), SuperUserAccess(), StateFilter(AddServerForm))
@router.callback_query(
    AdminPanel.Callback.filter(F.action == AdminPanelAction.servers), SuperUserAccess()
)
async def show_servers(
    query: CallbackQuery | Message, user: User, state: FSMContext | None = None
):
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
        await query.answer(text="Canceled!", reply_markup=ReplyKeyboardRemove())
    count = await Server.all().count()
    if count:
        servers = Servers(servers=await Server.all()).as_markup()
        if isinstance(query, CallbackQuery):
            return await query.message.edit_text(
                f"List of servers ({count}):",
                reply_markup=servers,
            )
        return await query.answer(
            f"List of servers ({count}):",
            reply_markup=servers,
        )
    servers = Servers(servers=[]).as_markup()
    if isinstance(query, CallbackQuery):
        return await query.message.edit_text(f"No server added!", reply_markup=servers)
    return await query.answer(f"No server added!", reply_markup=servers)


# Add Servers
@router.callback_query(
    Servers.Callback.filter(F.action == ServersAction.add_server),
    SuperUserAccess(),
)
async def add_server(query: CallbackQuery, user: User, state: FSMContext):
    await state.set_state(AddServerForm.name)
    await query.message.answer(
        "Enter a name for the server:",
        reply_markup=cancel_form,
    )


@router.message(AddServerForm.name, SuperUserAccess())
async def get_server_name(message: Message, user: User, state: FSMContext):
    if await Server.filter(name=message.text).first():
        return message.answer(
            "a server with this name already exists! try again:",
            reply_markup=cancel_form,
        )
    await state.update_data(name=message.text)
    await state.set_state(AddServerForm.host)
    await message.answer(
        "Enter domain or ip for the api server:",
        reply_markup=cancel_form,
    )


@router.message(AddServerForm.host, SuperUserAccess())
async def get_server_host(message: Message, user: User, state: FSMContext):
    # TODO: validate address
    await state.update_data(host=message.text)
    await state.set_state(AddServerForm.port)
    await message.answer(
        "Enter port of the api server(0 for not using a port):",
        reply_markup=cancel_form,
    )


@router.message(AddServerForm.port, SuperUserAccess())
async def get_server_port(message: Message, user: User, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer(
            "port number must be an integer! try again:",
            reply_markup=cancel_form,
        )
    await state.update_data(port=int(message.text))
    await state.set_state(AddServerForm.token)
    await message.answer(
        "enter the auth token for the api server", reply_markup=cancel_form
    )


@router.message(AddServerForm.token, SuperUserAccess())
async def get_server_token_handler(message: Message, user: User, state: FSMContext):
    await state.update_data(token=message.text)
    await state.set_state(AddServerForm.https)
    await message.answer("does the server supports https?", reply_markup=yes_or_no_form)


@router.message(AddServerForm.https, SuperUserAccess(), F.text.casefold() == "yes")
async def get_server_https_yes(message: Message, user: User, state: FSMContext):
    await state.update_data(https=True)
    await confirm_add_server(message, user, state)


@router.message(AddServerForm.https, SuperUserAccess(), F.text.casefold() == "no")
async def get_server_https_no(message: Message, user: User, state: FSMContext):
    await state.update_data(https=False)
    await confirm_add_server(message, user, state)


@router.message(AddServerForm.https, SuperUserAccess())
async def get_server_https_unknown(message: Message, user: User, state: FSMContext):
    await message.answer(
        text="Unknown answer! Please select one of the buttons:",
        reply_markup=yes_or_no_form,
    )


async def confirm_add_server(message: Message, user: User, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(AddServerForm.confirm)
    await message.answer(
        "is this data correct?\n"
        f"name: {data['name']}\n"
        f"host: {data['host']}\n"
        f"port: {data['port']}\n"
        f"token: <code>{data['token']}</code>\n"
        f"https: {data['https']}",
        reply_markup=yes_or_no_form,
    )


@router.message(AddServerForm.confirm, SuperUserAccess(), F.text.casefold() == "yes")
async def get_server_confirm_yes(message: Message, user: User, state: FSMContext):
    data = await state.get_data()
    server = Server(**data)
    client = AuthenticatedClient(base_url=server.url, token=server.token)
    try:  # test server
        await get_users_api_users_get.asyncio(client=client)
    except Exception as err:
        await message.answer(f"Aborting, could not connect to server! error: {err}")
        raise err
    await server.save()

    await message.reply(
        f"Server created:\nidentifier: {server.identifier}\nurl: {server.url}"
    )
    await Marzban.refresh_servers()
    await show_servers(message, user)


@router.message(AddServerForm.confirm, SuperUserAccess(), F.text.casefold() == "no")
async def get_server_confirm_no(message: Message, user: User, state: FSMContext):
    await state.set_state(AddServerForm.name)
    await message.answer(
        "Enter the data again!\nEnter a name for the server:",
        reply_markup=cancel_form,
    )


# Show Servers
@router.callback_query(
    Servers.Callback.filter(F.action == ServersAction.show), SuperUserAccess()
)
async def show_server(
    query: CallbackQuery,
    user: User,
    callback_data: Servers.Callback,
    state: FSMContext = None,
):
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
    server = await Server.filter(id=callback_data.server_id).first()
    if not server:
        await query.answer("Server not found!", show_alert=True)
        return await show_servers(
            query,
            user,
        )

    text = f"""
server id: <b>{server.id}</b>
server name: <b>{server.name}</b>
server url: <b>{server.url}</b>
is_enabled: <b>{server.is_enabled}</b>
server token: <code>{server.token}</code>
    """
    await query.message.edit_text(
        text, reply_markup=ServerAct(server).as_markup(), disable_web_page_preview=True
    )


# Remove Servers
@router.callback_query(
    ServerAct.Callback.filter(F.action == ServerActAction.rem),
    SuperUserAccess(),
)
async def remove_server(
    query: CallbackQuery, user: User, callback_data: ServerAct.Callback
):
    server = await Server.filter(id=callback_data.server_id).first()
    if not server:
        await query.answer("Server not found!", show_alert=True)
        return await show_servers(
            query,
            user,
        )

    if not callback_data.confirmed:
        await query.answer()
        text = """
Confirm removing server: 

❗️❗️<strong>be careful, this action is permenant and all the proxies will be deleted! you can also disable this server so no one could purchase from it.</strong>
"""
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmServerAction(
                server=server, action=ServerActAction.rem
            ).as_markup(),
        )
    await server.delete()
    await query.answer("Server Removed!", show_alert=True)
    return await show_servers(
        query,
        user,
    )


# Update Servers
@router.callback_query(
    ServerAct.Callback.filter(
        (F.action == ServerActAction.enable) | (F.action == ServerActAction.disable)
    ),
    SuperUserAccess(),
)
async def server_status_update(
    query: CallbackQuery, user: User, callback_data: ServerAct.Callback
):
    server = await Server.filter(id=callback_data.server_id).first()
    if not server:
        await query.answer("Server not found!", show_alert=True)
        return await show_servers(
            query,
            user,
        )

    if callback_data.action == ServerActAction.disable:
        if not server.is_enabled:
            await query.answer(f"Server is not enabled!", show_alert=True)
            return await show_server(
                query,
                user,
                callback_data=Servers.Callback(server_id=server.id, action="show"),
            )
        if not callback_data.confirmed:
            await query.answer()
            return await query.message.edit_text(
                "Confirm disabling server:",
                reply_markup=ConfirmServerAction(
                    server=server, action=ServerActAction.disable
                ).as_markup(),
            )
        server.is_enabled = False
        await server.save()
        await query.answer(f"Server disabled!", show_alert=True)
    elif callback_data.action == ServerActAction.enable:
        if server.is_enabled:
            await query.answer(f"Server is not disabled!", show_alert=True)
            return await show_server(
                query,
                user,
                callback_data=Servers.Callback(server_id=server.id, action="show"),
            )
        if not callback_data.confirmed:
            await query.answer()
            return await query.message.edit_text(
                "Confirm enabling server:",
                reply_markup=ConfirmServerAction(
                    server=server, action=ServerActAction.enable
                ).as_markup(),
            )
        server.is_enabled = True
        await server.save()
        await query.answer(f"Server enabled!", show_alert=True)
    return await show_server(
        query,
        user,
        callback_data=Servers.Callback(server_id=server.id, action="show"),
    )


@router.message(
    F.text.casefold() == "cancel", SuperUserAccess(), StateFilter(EditServerForm)
)
@router.callback_query(
    ServerAct.Callback.filter(F.action == ServerActAction.edit),
    SuperUserAccess(),
)
async def edit_server(
    query: CallbackQuery | Message,
    user: User,
    state: FSMContext,
    callback_data: ServerAct.Callback = None,
):
    if callback_data:
        server_id = callback_data.server_id
    else:
        server_id = (await state.get_data()).get("id")
    server = await Server.filter(id=server_id).first()
    if not server:
        if isinstance(query, CallbackQuery):
            await query.answer("Server not found!", show_alert=True)
            return await show_servers(
                query,
                user,
            )
        else:
            return await query.answer("Server not found!")

    await state.set_state(EditServerForm.id)
    data = await state.get_data()
    unsaved_changes = []
    for key, value in data.items():
        if server.__dict__.get(key) != value:
            unsaved_changes.append(key)
    await state.update_data(id=server.id)
    text = f"""
unsaved changes: {'-' if not unsaved_changes else ', '.join(unsaved_changes)}

server id: <b>{server.id}</b>
server name: <b>{data.get('name') or server.name}</b>
server host: <b>{data.get('host') or server.host}</b>
server port: <b>{data.get('port') or server.port}</b>
https: <b>{server.https if data.get('https') is None else data.get('https')}</b>
is_enabled: <b>{server.is_enabled}</b>

server token: <code>{data.get('token') or server.token}</code>
    """
    if isinstance(query, Message):
        return await query.answer(
            text, reply_markup=EditServer(server=server).as_markup()
        )
    return await query.message.edit_text(
        text, reply_markup=EditServer(server=server).as_markup()
    )


@router.callback_query(
    EditServer.Callback.filter(F.action == EditServerAction.save),
    SuperUserAccess(),
    StateFilter(EditServerForm),
)
async def edit_server_save(
    query: CallbackQuery,
    user: User,
    callback_data: EditServer.Callback,
    state: FSMContext,
):
    server = await Server.filter(id=callback_data.server_id).first()
    if not server:
        await query.answer("Server not found!", show_alert=True)
        return await show_servers(
            query,
            user,
        )
    data = await state.get_data()
    del data["id"]
    if not data:
        return await query.answer(f"Nothing changed! press cancel.", show_alert=True)

    await server.update_from_dict(data).save()
    await state.clear()
    await query.answer("Updated! fields: " + ", ".join(data), show_alert=True)
    await Marzban.refresh_servers()
    await show_server(
        query,
        user,
        callback_data=Servers.Callback(server_id=server.id, action=ServersAction.show),
        state=None,
    )


@router.callback_query(
    EditServer.Callback.filter(
        (F.action.in_(EditServerAction)) & ~(F.action == EditServerAction.save)
    ),
    SuperUserAccess(),
)
async def edit_server_action(
    query: CallbackQuery,
    user: User,
    callback_data: EditServer.Callback,
    state: FSMContext,
):
    server = await Server.filter(id=callback_data.server_id).first()
    if not server:
        await query.answer("Server not found!", show_alert=True)
        return await show_servers(
            query,
            user,
        )

    if callback_data.action == EditServerAction.name:
        await state.set_state(EditServerForm.name)
        await query.message.reply(
            "Enter new name for the server:",
            reply_markup=cancel_form,
        )
    elif callback_data.action == EditServerAction.host:
        await state.set_state(EditServerForm.host)
        await query.message.reply(
            "Enter new domain or ip for the api server:",
            reply_markup=cancel_form,
        )
    elif callback_data.action == EditServerAction.port:
        await state.set_state(EditServerForm.port)
        await query.message.reply(
            "Enter new port of the api server(0 for not using a port):",
            reply_markup=cancel_form,
        )
    elif callback_data.action == EditServerAction.token:
        await state.set_state(EditServerForm.token)
        await query.message.reply(
            "enter the new auth token for the api server", reply_markup=cancel_form
        )
    elif callback_data.action == EditServerAction.https:
        https = (await state.get_data()).get("https") or server.https
        if https:
            await state.update_data(https=False)
        else:
            await state.update_data(https=True)
        await edit_server(query, user, state)


@router.message(EditServerForm.name, SuperUserAccess())
async def edit_server_name(message: Message, user: User, state: FSMContext):
    server_id = (await state.get_data()).get("id")
    server = await Server.filter(id=int(server_id)).first()
    if not server:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    if server.name == message.text:
        return await message.answer(
            "the new name can't be the same as the old name! Enter again or press cancel."
        )

    if await Server.filter(name=message.text).exists():
        return message.answer(
            "a server with this name already exists! try again:",
            reply_markup=cancel_form,
        )

    await state.update_data(name=message.text)
    await edit_server(message, user, state)


@router.message(EditServerForm.host, SuperUserAccess())
async def edit_server_host(message: Message, user: User, state: FSMContext):
    server_id = (await state.get_data()).get("id")
    server = await Server.filter(id=int(server_id)).first()
    if not server:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    if server.host == message.text:
        return await message.answer(
            "the new host can't be the same as the old host! Enter again or press cancel."
        )
    await state.update_data(host=message.text)
    await edit_server(message, user, state)


@router.message(EditServerForm.port, SuperUserAccess())
async def edit_server_port(message: Message, user: User, state: FSMContext):
    server_id = (await state.get_data()).get("id")
    server = await Server.filter(id=int(server_id)).first()
    if not server:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    if not message.text.isdigit():
        return await message.answer(
            "port number must be an integer! try again:",
            reply_markup=cancel_form,
        )
    if server.port == int(message.text):
        return await message.answer(
            "the new port can't be the same as the old port! Enter again or press cancel."
        )
    await state.update_data(port=int(message.text))
    await edit_server(message, user, state)


@router.message(EditServerForm.token, SuperUserAccess())
async def edit_server_token(message: Message, user: User, state: FSMContext):
    server_id = (await state.get_data()).get("id")
    server = await Server.filter(id=int(server_id)).first()
    if not server:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    if server.token == message.text:
        return await message.answer(
            "the new token can't be the same as the old token! Enter again or press cancel."
        )
    await state.update_data(token=message.text)
    await edit_server(message, user, state)


# # Templates

# # Add Templates
# @router.callback_query(
#     Templates.Callback.filter(F.action == Templates.add),
#     IsSuperUser(),
# )
# async def add_template(query: CallbackQuery, user: User, state: FSMContext):
#     await state.set_state(AddTemplateForm.id)
#     await query.message.answer(
#         "Enter a name for the server:",
#         reply_markup=cancel_form,
#     )

# # Show Templates
# @router.callback_query(
#     ServerAct.Callback.filter(F.action == ServerActAction.templates),
#     IsSuperUser(),
# )
# async def show_templates(
#     query: CallbackQuery, user: User, callback_data: ServerAct.Callback
# ):
#     server = await Server.filter(id=callback_data.server_id).first()
#     if not server:
#         await query.answer("Server not found!", show_alert=True)
#         return await show_servers(
#             query,
#             user,
#         )

#     client = Marzban.get_server(server.id)
#     templates = await get_user_templates_api_user_template_get.asyncio(client=client)
#     if len(templates) < 1:
#         text = "No template Added!"
#         return await query.message.edit_text("No template added!", reply_markup=Templates(templates=[], server_id=server.id))
#     return await query.message.edit_text(f"Templates: ({len(templates)})", reply_markup=Templates(templates=templates, server_id=server.id))
