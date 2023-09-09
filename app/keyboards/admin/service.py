from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.server import Server
from app.models.service import Service

from .admin import AdminPanel, AdminPanelAction


class ServicesAction(str, Enum):
    show = "show"
    add = "add"
    save_new = "save_new"


class Services(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="services"):
        service_id: int = 0
        action: ServicesAction

    def __init__(self, services: list[Service], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for service in services:
            self.button(
                text=f"{service.name}",
                callback_data=self.Callback(
                    service_id=service.id, action=ServicesAction.show
                ),
            )
        self.button(
            text="Add Service",
            callback_data=self.Callback(action=ServicesAction.add),
        )
        self.button(
            text="Back",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.panel),
        )
        self.adjust(1, 1)


class ServiceActAction(str, Enum):
    rem = "rem"
    edit = "edit"
    flip_purchase = "flip_purchase"
    flip_renew = "flip_renew"
    flip_one_time_only = "flip_one_time_only"
    flip_resellers_only = "flip_resellers_only"
    flip_users_only = "flip_users_only"
    flip_is_test_service = "flip_is_test_service"
    cycle_flow = "cycle_flow"


class ServiceAct(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="srviceact"):
        service_id: int
        action: ServiceActAction
        confirmed: bool = False

    def __init__(self, service: Service, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text="Remove Service",
            callback_data=self.Callback(
                service_id=service.id, action=ServiceActAction.rem
            ),
        )
        self.button(
            text=f"Purchase: {'✅' if service.purchaseable else '❌'}",
            callback_data=self.Callback(
                service_id=service.id, action=ServiceActAction.flip_purchase
            ),
        )
        self.button(
            text=f"Renew: {'✅' if service.renewable else '❌'}",
            callback_data=self.Callback(
                service_id=service.id, action=ServiceActAction.flip_renew
            ),
        )
        self.button(
            text=f"One time only: {'✅' if service.one_time_only else '❌'}",
            callback_data=self.Callback(
                service_id=service.id, action=ServiceActAction.flip_one_time_only
            ),
        )
        self.button(
            text=f"Test service: {'✅' if service.is_test_service else '❌'}",
            callback_data=self.Callback(
                service_id=service.id, action=ServiceActAction.flip_is_test_service
            ),
        )
        self.button(
            text=f"flow: {service.flow}",
            callback_data=self.Callback(
                service_id=service.id, action=ServiceActAction.cycle_flow
            ),
        )
        self.button(
            text="Edit Service",
            callback_data=self.Callback(
                service_id=service.id, action=ServiceActAction.edit
            ),
        )
        self.button(
            text="Back",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.services),
        )
        self.adjust(1, 2, 2, 1)


class ConfirmServiceAction(InlineKeyboardBuilder):
    def __init__(
        self, service: Service, action: ServiceActAction, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.button(
            text="confirm",
            callback_data=ServiceAct.Callback(
                service_id=service.id, action=action, confirmed=True
            ),
        )
        self.button(
            text=f"Back",
            callback_data=Services.Callback(
                service_id=service.id, action=ServicesAction.show
            ),
        )


class SelectServer(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="slctsrv"):
        server_id: int

    def __init__(self, servers: list[Server], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for server in servers:
            self.button(
                text=f"{server.name} | {server.host}",
                callback_data=self.Callback(server_id=server.id),
            )
        self.button(
            text="cancel",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.services),
        )
        self.adjust(1, 1)


class SelectInbounds(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="slctinbnd"):
        server_id: int
        protocol: str
        inbound: str | None = None
        for_edit: bool = False
        service_id: int | None = None

    def __init__(
        self,
        inbounds: dict[str, list[str]],
        selected_inbounds: dict[str, list[str]],
        server_id: int,
        for_edit: bool = False,
        service_id: int = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        for protocol, protocol_inbounds in inbounds.items():
            if protocol in selected_inbounds:
                self.button(
                    text=f"✅ {protocol.upper()}",
                    callback_data=self.Callback(
                        server_id=server_id,
                        protocol=protocol,
                        for_edit=for_edit,
                        service_id=service_id,
                    ),
                )
                for inbound in protocol_inbounds:
                    self.button(
                        text=f"{'✅' if inbound in selected_inbounds[protocol] else '❌'} {inbound}",
                        callback_data=self.Callback(
                            server_id=server_id,
                            protocol=protocol,
                            inbound=inbound,
                            for_edit=for_edit,
                            service_id=service_id,
                        ),
                    )
            else:
                self.button(
                    text=f"❌ {protocol}",
                    callback_data=self.Callback(
                        server_id=server_id,
                        protocol=protocol,
                        for_edit=for_edit,
                        service_id=service_id,
                    ),
                )
        self.button(
            text="Save",
            callback_data=Services.Callback(
                server_id=server_id, action=ServicesAction.save_new
            )
            if not for_edit
            else ServiceAct.Callback(
                service_id=service_id, action=ServiceActAction.edit
            ),
        )
        self.button(
            text="cancel",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.services),
        )
        self.adjust(1, 1, 1)


class EditServiceAction(str, Enum):
    data_limit = "edit_data_lmit"
    expire_duration = "edit_expire_duration"
    price = "edit_price"
    name = "edit_name"
    inbounds = "edit_inbounds"
    save_inbounds = "save_inbounds"
    save = "save"


class EditService(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="editsrvic"):
        service_id: int
        action: EditServiceAction

    def __init__(self, service: Service, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for action in EditServiceAction:
            if not action.value.startswith("edit_"):
                continue
            self.button(
                text=f"Edit {action.name.capitalize()}",
                callback_data=self.Callback(service_id=service.id, action=action),
            )
        self.button(
            text="Save",
            callback_data=self.Callback(
                service_id=service.id, action=EditServiceAction.save
            ),
        )
        self.button(
            text=f"Cancel",
            callback_data=Services.Callback(
                service_id=service.id, action=ServicesAction.show
            ),
        )
        self.adjust(1, 1, 2, 1, 1)
