from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.server import Server

from .admin import AdminPanel, AdminPanelAction


class ServersAction(str, Enum):
    show = "show"
    add_server = "add_server"


class Servers(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="servers"):
        server_id: int = 0
        action: ServersAction

    def __init__(self, servers: list[Server], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for server in servers:
            self.button(
                text=f"{server.name} | {server.host}",
                callback_data=self.Callback(
                    server_id=server.id, action=ServersAction.show
                ),
            )
        self.button(
            text="Add Server",
            callback_data=self.Callback(action=ServersAction.add_server),
        )
        self.button(
            text="Back",
            callback_data=AdminPanel.Callback(action=AdminPanelAction.panel),
        )
        self.adjust(1, 1)


class ServerActAction(str, Enum):
    rem = "rem"
    disable = "disable"
    enable = "enable"
    edit = "edit"


class ServerAct(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="srvact"):
        server_id: int
        action: ServerActAction
        confirmed: bool = False

    def __init__(self, server: Server, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button(
            text="Remove Server",
            callback_data=self.Callback(
                server_id=server.id, action=ServerActAction.rem
            ),
        )
        if server.is_enabled:
            self.button(
                text="Disable Server",
                callback_data=self.Callback(
                    server_id=server.id, action=ServerActAction.disable
                ),
            )
        else:
            self.button(
                text="Enable Server",
                callback_data=self.Callback(
                    server_id=server.id, action=ServerActAction.enable
                ),
            )

        self.button(
            text="Edit Server",
            callback_data=self.Callback(
                server_id=server.id, action=ServerActAction.edit
            ),
        )
        self.button(text="Back", callback_data=AdminPanel.Callback(action="servers"))
        self.adjust(1, 2, 2, 1)


class ConfirmServerAction(InlineKeyboardBuilder):
    def __init__(
        self, server: Server, action: ServerActAction, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.button(
            text="confirm",
            callback_data=ServerAct.Callback(
                server_id=server.id, action=action, confirmed=True
            ),
        )
        self.button(
            text=f"Back",
            callback_data=Servers.Callback(
                server_id=server.id, action=ServersAction.show
            ),
        )


class EditServerAction(str, Enum):
    host = "edit_host"
    port = "edit_port"
    token = "edit_token"
    name = "edit_name"
    https = "https"
    save = "save"


class EditServer(InlineKeyboardBuilder):
    class Callback(CallbackData, prefix="editsrv"):
        server_id: int
        action: EditServerAction

    def __init__(self, server: Server, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for action in EditServerAction:
            if not action.value.startswith("edit_"):
                continue
            self.button(
                text=f"Edit {action.name.capitalize()}",
                callback_data=self.Callback(server_id=server.id, action=action),
            )
        self.button(
            text=f"flip HTTPS",
            callback_data=self.Callback(
                server_id=server.id, action=EditServerAction.https
            ),
        )
        self.button(
            text="Save",
            callback_data=self.Callback(
                server_id=server.id, action=EditServerAction.save
            ),
        )
        self.button(
            text=f"Cancel",
            callback_data=Servers.Callback(
                server_id=server.id, action=ServersAction.show
            ),
        )
        self.adjust(2, 2, 1, 1)


# class TemplatesAction(str, Enum):
#     show = "show"
#     add = "add"


# class Templates(InlineKeyboardBuilder):
#     class Callback(CallbackData, prefix="addtmplt"):
#         server_id: int
#         template_id: int = 0
#         action: TemplatesAction

#     def __init__(
#         self, templates: list[UserTemplateResponse], server_id: int, *args, **kwargs
#     ) -> None:
#         super().__init__(*args, **kwargs)
#         for template in templates:
#             self.button(
#                 text=f"{template.id} | {template.name}",
#                 callback_data=self.Callback(
#                     server_id=server_id,
#                     template_id=template.id,
#                     action=TemplatesAction.show,
#                 ),
#             )
#         self.button(
#             text="Add Template",
#             callback_data=self.Callback(
#                 server_id=server_id, action=TemplatesAction.add
#             ),
#         )
#         self.button(
#             text="back",
#             callback_data=Servers.Callback(
#                 server_id=server_id, action=ServersAction.show
#             ),
#         )
#         self.adjust(1, 1, 1)
