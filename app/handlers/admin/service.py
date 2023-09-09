import re

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
from app.keyboards.admin.service import (
    ConfirmServiceAction,
    EditService,
    EditServiceAction,
    SelectInbounds,
    SelectServer,
    ServiceAct,
    ServiceActAction,
    Services,
    ServicesAction,
)
from app.marzban import Marzban
from app.models.server import Server
from app.models.service import Service
from app.models.user import User
from app.utils import helpers
from app.utils.filters import SuperUserAccess
from marzban_client.api.system import get_inbounds_api_inbounds_get

from . import router

cancel_form = CancelFormAdmin().as_markup(resize_keyboard=True, one_time_only=True)
yes_or_no_form = YesOrNoFormAdmin().as_markup(
    resize_keyboard=True, one_time_keyboard=True
)


class AddServiceForm(StatesGroup):
    name = State()
    data_limit = State()
    expire_duration = State()
    server_id = State()
    inbounds = State()
    price = State()
    confirm = State()


class EditServiceForm(StatesGroup):
    id = State()
    name = State()
    data_limit = State()
    expire_duration = State()
    inbounds = State()
    price = State()


@router.message(
    F.text.casefold() == "cancel", SuperUserAccess(), StateFilter(AddServiceForm)
)
@router.message(Command("cancel"), SuperUserAccess(), StateFilter(AddServiceForm))
@router.callback_query(
    AdminPanel.Callback.filter(F.action == AdminPanelAction.services), SuperUserAccess()
)
async def show_services(
    query: CallbackQuery | Message, user: User, state: FSMContext | None = None
):
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
        await query.answer(text="Canceled!", reply_markup=ReplyKeyboardRemove())
    count = await Service.all().count()
    if count:
        servers = Services(services=await Service.all()).as_markup()
        if isinstance(query, CallbackQuery):
            return await query.message.edit_text(
                f"List of services ({count}):",
                reply_markup=servers,
            )
        return await query.answer(
            f"List of services ({count}):",
            reply_markup=servers,
        )
    services = Services(services=[]).as_markup()
    if isinstance(query, CallbackQuery):
        return await query.message.edit_text(
            f"No service added!", reply_markup=services
        )
    return await query.answer(f"No service added!", reply_markup=services)


# Add Services
@router.callback_query(
    Services.Callback.filter(F.action == ServicesAction.add),
    SuperUserAccess(),
)
async def add_service(query: CallbackQuery, user: User, state: FSMContext):
    await state.set_state(AddServiceForm.name)
    await query.message.answer(
        "Enter a name for the service:",
        reply_markup=cancel_form,
    )


@router.message(AddServiceForm.name, SuperUserAccess())
async def get_service_name(message: Message, user: User, state: FSMContext):
    if await Service.filter(name=message.text).first():
        return message.answer(
            "a service with this name already exists! try again:",
            reply_markup=cancel_form,
        )
    await state.update_data(name=message.text)
    await state.set_state(AddServiceForm.data_limit)
    await message.answer(
        "Enter data_limit for the service(in GB, 0 for unlimited):",
        reply_markup=cancel_form,
    )


@router.message(AddServiceForm.data_limit, SuperUserAccess())
async def get_service_data_limit(message: Message, user: User, state: FSMContext):
    try:
        if float(message.text) < 0:
            return await message.answer(
                message.chat.id,
                "❌ Data limit must be greater or equal to 0.",
                reply_markup=cancel_form(),
            )
        data_limit = float(message.text) * 1024 * 1024 * 1024
    except ValueError:
        return await message.answer(
            "data_limit must be an integer or float! try again:",
            reply_markup=cancel_form,
        )
    await state.update_data(data_limit=data_limit)
    await state.set_state(AddServiceForm.expire_duration)
    await message.answer(
        "'⬆️ Enter Expire Duration You Can Use Regex Symbol: ^[0-9]{1,3}(D|M|Y|H) :\n⚠️ Send 0 for never expire.'",
        reply_markup=cancel_form,
    )


@router.message(AddServiceForm.expire_duration, SuperUserAccess())
async def get_service_expire_duration(message: Message, user: User, state: FSMContext):
    try:
        if message.text.isnumeric() and int(message.text) == 0:
            expire_duration = None
        if re.match(r"^[0-9]{1,3}(M|m|Y|y|D|d|H|h)$", message.text):
            expire_duration = 0
            number_pattern = r"^[0-9]{1,3}"
            number = int(re.findall(number_pattern, message.text)[0])
            symbol_pattern = r"(M|m|Y|y|D|d|H|h)$"
            symbol = re.findall(symbol_pattern, message.text)[0].upper()
            if symbol == "H":
                expire_duration = 3600 * number
            elif symbol == "D":
                expire_duration += 86400 * number
            elif symbol == "M":
                expire_duration += 2592000 * number
            elif symbol == "Y":
                expire_duration = 31104000 * number
        else:
            raise ValueError("Could not parse expire_duration")
    except ValueError:
        return await message.answer(
            "❌ Expire duration must be in 1m or 2m or 1d, Regex Symbol: ^[0-9]{1,3}(D|M|Y|H)",
            reply_markup=cancel_form,
        )
    await state.update_data(expire_duration=expire_duration)
    await state.set_state(AddServiceForm.price)
    await message.answer("Enter price for this service:", reply_markup=cancel_form)


@router.message(AddServiceForm.price, SuperUserAccess())
async def get_service_price(message: Message, user: User, state: FSMContext):
    try:
        await state.update_data(price=int(message.text))
        await state.set_state(AddServiceForm.server_id)
        servers = await Server.all()
        await message.answer(
            "Selecet a server for this service:",
            reply_markup=SelectServer(servers=servers).as_markup(),
        )
    except ValueError:
        return await message.answer("Price must be integer! enter again:")


@router.callback_query(
    AddServiceForm.server_id, SuperUserAccess(), SelectServer.Callback.filter()
)
async def get_service_server_id(
    query: CallbackQuery,
    user: User,
    state: FSMContext,
    callback_data: SelectServer.Callback,
):
    try:
        client = Marzban.get_server(callback_data.server_id)
    except KeyError:
        return await query.answer(
            text=f"Could not get server {callback_data.server_id!r} api client!"
        )
    inbounds: dict[str, list[str]] = {
        protocol: [inbound.tag for inbound in protocol_inbounds]
        for protocol, protocol_inbounds in (
            await get_inbounds_api_inbounds_get.asyncio(client=client)
        ).additional_properties.items()
    }
    await state.update_data(server_id=callback_data.server_id)
    data = await state.get_data()

    text = f"""
name: <b>{data.get('name')}</b>
data_limit: <b>{helpers.hr_size(data.get('data_limit')) if data.get('data_limit') else 'Unlimited'}</b>
expire_duration: <b>{helpers.hr_time(data.get('expire_duration')) if data.get('expire_duration') else 'Never'}</b>
price: <b>{data.get('price')}</b>
server_id: <b>{data.get('server_id')}</b>
    """
    await state.set_state(AddServiceForm.inbounds)
    await query.message.edit_text(
        text,
        reply_markup=SelectInbounds(
            inbounds=inbounds,
            selected_inbounds={},
            server_id=callback_data.server_id,
        ).as_markup(),
    )


@router.callback_query(
    EditServiceForm.inbounds,
    SuperUserAccess(),
    SelectInbounds.Callback.filter(F.for_edit == True),
)
@router.callback_query(
    AddServiceForm.inbounds,
    SuperUserAccess(),
    SelectInbounds.Callback.filter(F.for_edit == False),
)
async def select_service_inbounds(
    query: CallbackQuery,
    user: User,
    state: FSMContext,
    callback_data: SelectInbounds.Callback,
):
    data = await state.get_data()
    selected_inbounds: dict[str, list[str]] = data.get("inbounds", dict())

    try:
        client = Marzban.get_server(callback_data.server_id)
    except KeyError:
        return await query.answer(
            text=f"Could not get server {callback_data.server_id!r} api client!"
        )
    inbounds: dict[str, list[str]] = {
        protocol: [inbound.tag for inbound in protocol_inbounds]
        for protocol, protocol_inbounds in (
            await get_inbounds_api_inbounds_get.asyncio(client=client)
        ).additional_properties.items()
    }

    if callback_data.inbound is None:
        if callback_data.protocol not in selected_inbounds:
            selected_inbounds.update(
                {callback_data.protocol: inbounds[callback_data.protocol].copy()}
            )
        else:
            del selected_inbounds[callback_data.protocol]
    else:
        if callback_data.protocol not in selected_inbounds:
            selected_inbounds.update(
                {callback_data.protocol: inbounds[callback_data.protocol].copy()}
            )
        else:
            if callback_data.inbound not in selected_inbounds[callback_data.protocol]:
                selected_inbounds[callback_data.protocol].append(callback_data.inbound)
            else:
                selected_inbounds[callback_data.protocol].remove(callback_data.inbound)
                if not selected_inbounds[
                    callback_data.protocol
                ]:  # delete protocol with no inbound
                    del selected_inbounds[callback_data.protocol]
    await state.update_data(inbounds=selected_inbounds)

    if not callback_data.for_edit:
        text = f"""
name: <b>{data.get('name')}</b>
data_limit: <b>{helpers.hr_size(data.get('data_limit')) if data.get('data_limit') else 'Unlimited'}</b>
expire_duration: <b>{helpers.hr_time(data.get('expire_duration')) if data.get('expire_duration') else 'Never'}</b>
price: <b>{data.get('price')}</b>
server_id: <b>{data.get('server_id')}</b>

inbounds: <code>{selected_inbounds}</code>
        """
        return await query.message.edit_text(
            text,
            reply_markup=SelectInbounds(
                inbounds=inbounds,
                selected_inbounds=selected_inbounds,
                server_id=callback_data.server_id,
            ).as_markup(),
        )
    return await query.message.edit_text(
        f"select inbounds and press save:\n\ninbounds: <code>{selected_inbounds}</code>",
        reply_markup=SelectInbounds(
            inbounds=inbounds,
            selected_inbounds=selected_inbounds,
            server_id=callback_data.server_id,
            for_edit=True,
            service_id=callback_data.service_id,
        ).as_markup(),
    )


@router.callback_query(
    AddServiceForm.inbounds,
    SuperUserAccess(),
    Services.Callback.filter(F.action == ServicesAction.save_new),
)
async def save_new_service(
    query: CallbackQuery,
    user: User,
    state: FSMContext,
    callback_data: SelectInbounds.Callback,
):
    data = await state.get_data()
    selected_inbounds: dict[str, list[str]] = data.get("inbounds")

    if not selected_inbounds:
        return await query.answer("No inbound protocol selected!", show_alert=True)

    if not any(
        [False if not inbounds else True for inbounds in selected_inbounds.values()]
    ):
        return await query.answer("No inbound selected!", show_alert=True)

    await state.clear()
    service = await Service.create(
        name=data.get("name"),
        data_limit=data.get("data_limit"),
        expire_duration=data.get("expire_duration"),
        price=data.get("price"),
        inbounds=selected_inbounds,
        server_id=data.get("server_id"),
    )
    await show_service(
        query,
        user,
        callback_data=Services.Callback(
            service_id=service.id, action=ServicesAction.show
        ),
        state=state,
    )


# Show Services
@router.callback_query(
    SuperUserAccess(),
    Services.Callback.filter(F.action == ServicesAction.show),
)
async def show_service(
    query: CallbackQuery,
    user: User,
    callback_data: Services.Callback,
    state: FSMContext | None = None,
):
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
    service = (
        await Service.filter(id=callback_data.service_id)
        .prefetch_related("server")
        .first()
    )
    if not service:
        await query.answer("Service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    text = f"""
service id: <b>{service.id}</b>
service name: <b>{service.name}</b>
service data_limit: <b>{helpers.hr_size(service.data_limit)}</b>
service expire_duration: <code>{helpers.hr_time(service.expire_duration)}</code>
service price: <b>{service.price}</b>
server: <b>{service.server.name}</b> ({service.server.id})
inbounds: {service.inbounds}
    """
    await query.message.edit_text(
        text, reply_markup=ServiceAct(service=service).as_markup()
    )


# Remove Services
@router.callback_query(
    ServiceAct.Callback.filter(F.action == ServiceActAction.rem),
    SuperUserAccess(),
)
async def remove_service(
    query: CallbackQuery, user: User, callback_data: ServiceAct.Callback
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("Service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    if not callback_data.confirmed:
        await query.answer()
        text = """
Confirm removing service: 

❗️❗️<strong>be careful, this action is permenant and field of server_id for all the proxies will be set to null! you can also disable this service so no one could purchase from it.</strong>
"""
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmServiceAction(
                service=service, action=ServiceActAction.rem
            ).as_markup(),
        )
    await service.delete()
    await query.answer("Service Removed!", show_alert=True)
    return await show_services(
        query,
        user,
    )


# update Services
@router.callback_query(
    ServiceAct.Callback.filter(F.action == ServiceActAction.cycle_flow),
    SuperUserAccess(),
)
async def service_cycle_flow(
    query: CallbackQuery, user: User, callback_data: ServiceAct.Callback
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("Service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    try:
        f = iter(Service.ServiceProxyFlow)
        while next(f) != service.flow:
            pass
        service.flow = next(f)
    except StopIteration:
        service.flow = next(iter(Service.ServiceProxyFlow))  # get first enum value

    await service.save()
    await query.answer(
        f"flow set to {service.flow}. it only affects protocols that support 'flow'!",
        show_alert=True,
    )
    await show_service(
        query,
        user,
        callback_data=Services.Callback(
            service_id=service.id, action=ServicesAction.show
        ),
    )


@router.callback_query(
    ServiceAct.Callback.filter(F.action == ServiceActAction.flip_purchase),
    SuperUserAccess(),
)
async def edit_service_purchase(
    query: CallbackQuery, user: User, callback_data: ServiceAct.Callback
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("Service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    if not callback_data.confirmed:
        await query.answer()
        if service.purchaseable:
            text = """
Confirm disable purchasing: 

❗️❗️<strong>be careful, if you do this no one can purchase this service anymore.</strong>
            """
        else:
            text = """
Confirm enabling purchasing: 

❗️❗️<strong>be careful, if you do this users can purchase this service.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmServiceAction(
                service=service,
                action=ServiceActAction.flip_purchase,
            ).as_markup(),
        )
    if service.purchaseable:
        service.purchaseable = False
        text = "purchase disabled!"
    else:
        service.purchaseable = True
        text = "purchase enabled!"
    await service.save()
    await query.answer(text, show_alert=True)
    await show_service(
        query,
        user,
        callback_data=Services.Callback(
            service_id=service.id, action=ServicesAction.show
        ),
    )


@router.callback_query(
    ServiceAct.Callback.filter(F.action == ServiceActAction.flip_renew),
    SuperUserAccess(),
)
async def edit_service_renew(
    query: CallbackQuery, user: User, callback_data: ServiceAct.Callback
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("Service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    if not callback_data.confirmed:
        await query.answer()
        if service.renewable:
            text = """
Confirm disable purchasing: 

❗️❗️<strong>be careful, if you do this no one can renew this service anymore.</strong>
            """
        else:
            text = """
Confirm enabling purchasing: 

❗️❗️<strong>be careful, if you do this users can renew this service.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmServiceAction(
                service=service,
                action=ServiceActAction.flip_renew,
            ).as_markup(),
        )
    if service.renewable:
        service.renewable = False
        text = "renew disabled!"
    else:
        service.renewable = True
        text = "renew enabled!"
    await service.save()
    await query.answer(text, show_alert=True)
    await show_service(
        query,
        user,
        callback_data=Services.Callback(
            service_id=service.id, action=ServicesAction.show
        ),
    )


@router.callback_query(
    ServiceAct.Callback.filter(F.action == ServiceActAction.flip_one_time_only),
    SuperUserAccess(),
)
async def edit_service_one_time_only(
    query: CallbackQuery, user: User, callback_data: ServiceAct.Callback
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("Service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    if not callback_data.confirmed:
        await query.answer()
        if service.one_time_only:
            text = """
Confirm disabling one_time_only: 

❗️❗️<strong>be careful, if you do this users can activate this service more than once.</strong>
            """
        else:
            text = """
Confirm enabling one_time_only: 

❗️❗️<strong>be careful, if you do this users can activate this service only once.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmServiceAction(
                service=service,
                action=ServiceActAction.flip_one_time_only,
            ).as_markup(),
        )
    if service.one_time_only:
        service.one_time_only = False
        text = "one time only disabled!"
    else:
        service.one_time_only = True
        text = "one time only enabled!"
    await service.save()
    await query.answer(text, show_alert=True)
    await show_service(
        query,
        user,
        callback_data=Services.Callback(
            service_id=service.id, action=ServicesAction.show
        ),
    )


@router.callback_query(
    ServiceAct.Callback.filter(F.action == ServiceActAction.flip_is_test_service),
    SuperUserAccess(),
)
async def edit_service_is_test_service(
    query: CallbackQuery, user: User, callback_data: ServiceAct.Callback
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("Service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    if not callback_data.confirmed:
        await query.answer()
        if service.is_test_service:
            text = """
Confirm disabling is_test_service: 

❗️❗️<strong>be careful, if you do this users can activate this service more than once.</strong>
            """
        else:
            text = """
Confirm enabling is_test_service: 

❗️❗️<strong>be careful, if you do this users can activate this service only once.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmServiceAction(
                service=service,
                action=ServiceActAction.flip_is_test_service,
            ).as_markup(),
        )
    if service.is_test_service:
        service.is_test_service = False
        text = "is test service disabled!"
    else:
        service.is_test_service = True
        text = "is test service enabled!"
    await service.save()
    await query.answer(text, show_alert=True)
    await show_service(
        query,
        user,
        callback_data=Services.Callback(
            service_id=service.id, action=ServicesAction.show
        ),
    )


@router.message(
    F.text.casefold() == "cancel", SuperUserAccess(), StateFilter(EditServiceForm)
)
@router.callback_query(
    ServiceAct.Callback.filter(F.action == ServiceActAction.edit),
    SuperUserAccess(),
)
async def edit_service(
    query: CallbackQuery | Message,
    user: User,
    state: FSMContext,
    callback_data: ServiceAct.Callback = None,
):
    if callback_data:
        service_id = callback_data.service_id
    else:
        service_id = (await state.get_data()).get("id")
    service = await Service.filter(id=service_id).first()
    if not service:
        if isinstance(query, CallbackQuery):
            await query.answer("Service not found!", show_alert=True)
            return await show_services(
                query,
                user,
            )
        else:
            return await query.answer("Service not found!")

    await state.set_state(EditServiceForm.id)
    data = await state.get_data()
    unsaved_changes = []
    for key, value in data.items():
        if service.__dict__.get(key) != value:
            unsaved_changes.append(key)
    await state.update_data(id=service.id)
    text = f"""
unsaved changes: {'-' if not unsaved_changes else ', '.join(unsaved_changes)}

service id: <b>{service.id}</b>
service name: <b>{data.get('name') or service.name}</b>
service data_limit: <b>{helpers.hr_size(data.get('data_limit') or service.data_limit)}</b>
service expire_duration: <code>{helpers.hr_time(data.get('expire_duration') or service.expire_duration)}</code>
service price: <b>{data.get('price') or service.price}</b>
inbounds: <code>{service.inbounds if data.get('inbounds') is None else data.get('inbounds')}</code>
    """
    if isinstance(query, Message):
        return await query.answer(
            text, reply_markup=EditService(service=service).as_markup()
        )
    return await query.message.edit_text(
        text, reply_markup=EditService(service=service).as_markup()
    )


@router.callback_query(
    EditService.Callback.filter(F.action == EditServiceAction.save),
    SuperUserAccess(),
    StateFilter(EditServiceForm),
)
async def edit_service_save(
    query: CallbackQuery,
    user: User,
    callback_data: EditService.Callback,
    state: FSMContext,
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )
    data = await state.get_data()
    del data["id"]
    if not data:
        return await query.answer(f"Nothing changed! press cancel.", show_alert=True)

    selected_inbounds: dict[str, list[str]] = data.get("inbounds") or service.inbounds
    if not selected_inbounds:
        return await query.answer("No inbound protocol selected!", show_alert=True)

    if not any(
        [False if not inbounds else True for inbounds in selected_inbounds.values()]
    ):
        return await query.answer("No inbound selected!", show_alert=True)

    await service.update_from_dict(data).save()
    await state.clear()
    await query.answer("Updated! fields: " + ", ".join(data), show_alert=True)
    await show_service(
        query,
        user,
        callback_data=Services.Callback(
            service_id=service.id, action=ServicesAction.show
        ),
        state=None,
    )


@router.callback_query(
    EditService.Callback.filter(
        (F.action.in_(EditServiceAction)) & ~(F.action == EditServiceAction.save)
    ),
    SuperUserAccess(),
)
async def edit_server_action(
    query: CallbackQuery,
    user: User,
    callback_data: EditService.Callback,
    state: FSMContext,
):
    service = await Service.filter(id=callback_data.service_id).first()
    if not service:
        await query.answer("service not found!", show_alert=True)
        return await show_services(
            query,
            user,
        )

    if callback_data.action == EditServiceAction.name:
        await state.set_state(EditServiceForm.name)
        await query.message.reply(
            "Enter new name for the Service:",
            reply_markup=cancel_form,
        )
    elif callback_data.action == EditServiceAction.data_limit:
        await state.set_state(EditServiceForm.data_limit)
        await query.message.reply(
            "Enter new data_limit for the service(in GB, 0 for unlimited):",
            reply_markup=cancel_form,
        )
    elif callback_data.action == EditServiceAction.expire_duration:
        await state.set_state(EditServiceForm.expire_duration)
        await query.message.reply(
            "'⬆️ Enter new Expire Duration You Can Use Regex Symbol: ^[0-9]{1,3}(D|M|Y) :\n⚠️ Send 0 for never expire.'",
            reply_markup=cancel_form,
        )
    elif callback_data.action == EditServiceAction.price:
        await state.set_state(EditServiceForm.price)
        await query.message.reply(
            "Enter new price for this service:", reply_markup=cancel_form
        )
    elif callback_data.action == EditServiceAction.inbounds:
        client = Marzban.get_server(service.server_id)
        inbounds: dict[str, list[str]] = {
            protocol: [inbound.tag for inbound in protocol_inbounds]
            for protocol, protocol_inbounds in (
                await get_inbounds_api_inbounds_get.asyncio(client=client)
            ).additional_properties.items()
        }

        await state.set_state(EditServiceForm.inbounds)
        await query.message.edit_text(
            "select inbounds and press save:",
            reply_markup=SelectInbounds(
                inbounds=inbounds,
                selected_inbounds=service.inbounds,
                server_id=service.server_id,
                for_edit=True,
                service_id=service.id,
            ).as_markup(),
        )


@router.message(EditServiceForm.name, SuperUserAccess())
async def get_service_name(message: Message, user: User, state: FSMContext):
    service_id = (await state.get_data()).get("id")
    service = await Service.filter(id=int(service_id)).first()
    if not service:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    if service.name == message.text:
        return await message.answer(
            "the new name can't be the same as the old name! Enter again or press cancel."
        )

    if await Service.filter(name=message.text).exists():
        return message.answer(
            "a service with this name already exists! try again:",
            reply_markup=cancel_form,
        )

    await state.update_data(name=message.text)
    await edit_service(message, user, state)


@router.message(EditServiceForm.data_limit, SuperUserAccess())
async def get_service_data_limit(message: Message, user: User, state: FSMContext):
    service_id = (await state.get_data()).get("id")
    service = await Service.filter(id=int(service_id)).first()
    if not service:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    try:
        if float(message.text) < 0:
            return await message.answer(
                message.chat.id,
                "❌ Data limit must be greater or equal to 0.",
                reply_markup=cancel_form(),
            )
        data_limit = float(message.text) * 1024 * 1024 * 1024
    except ValueError:
        return await message.answer(
            "data_limit must be an integer or float! try again:",
            reply_markup=cancel_form,
        )
    if service.data_limit == data_limit:
        return await message.answer(
            "the new data_limit can't be the same as the old data_limit! Enter again or press cancel."
        )
    await state.update_data(data_limit=data_limit)
    await edit_service(message, user, state)


@router.message(EditServiceForm.expire_duration, SuperUserAccess())
async def get_service_expire_duration(message: Message, user: User, state: FSMContext):
    service_id = (await state.get_data()).get("id")
    service = await Service.filter(id=int(service_id)).first()
    if not service:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    try:
        if message.text.isnumeric() and int(message.text) == 0:
            expire_duration = None
        if re.match(r"^[0-9]{1,3}(M|m|Y|y|D|d|H|h)$", message.text):
            expire_duration = 0
            number_pattern = r"^[0-9]{1,3}"
            number = int(re.findall(number_pattern, message.text)[0])
            symbol_pattern = r"(M|m|Y|y|D|d|H|h)$"
            symbol = re.findall(symbol_pattern, message.text)[0].upper()
            if symbol == "H":
                expire_duration = 3600 * number
            elif symbol == "D":
                expire_duration += 86400 * number
            elif symbol == "M":
                expire_duration += 2592000 * number
            elif symbol == "Y":
                expire_duration = 31104000 * number
        else:
            raise ValueError("Could not parse expire_duration")
    except ValueError:
        return await message.answer(
            "❌ Expire duration must be in 1m or 2m or 1d, Regex Symbol: ^[0-9]{1,3}(D|M|Y|H)",
            reply_markup=cancel_form,
        )
    if service.expire_duration == expire_duration:
        return await message.answer(
            "the new expire_duration can't be the same as the old expire_duration! Enter again or press cancel."
        )
    await state.update_data(expire_duration=expire_duration)
    await edit_service(message, user, state)


@router.message(EditServiceForm.price, SuperUserAccess())
async def get_service_price(message: Message, user: User, state: FSMContext):
    service_id = (await state.get_data()).get("id")
    service = await Service.filter(id=int(service_id)).first()
    if not service:
        await state.clear()
        return await message.answer(
            "An error occured! open a new panel with '/admin' and try again."
        )
    try:
        price = int(message.text)
    except ValueError:
        return await message.answer("Price must be integer! enter again:")

    if service.price == price:
        return await message.answer(
            "the new price can't be the same as the old price! Enter again or press cancel."
        )
    await state.update_data(price=price)
    await edit_service(message, user, state)
