from enum import Enum
from typing import TYPE_CHECKING

from tortoise import fields

from . import TimedBase

if TYPE_CHECKING:
    from .server import Server
    from .service import Service
    from .user import Invoice, User


class ProxyStatus(Enum):
    active = "active"
    disabled = "disabled"
    limited = "limited"
    expired = "expired"


class Proxy(TimedBase):
    class Meta:
        table = "proxies"

    id = fields.IntField(pk=True)
    custom_name = fields.CharField(max_length=64, null=True)
    username = fields.CharField(max_length=32, null=False, index=True, unique=True)
    cost = fields.IntField(null=True)
    status = fields.CharEnumField(
        ProxyStatus, max_length=12, default=ProxyStatus.active
    )
    renewed_at = fields.DatetimeField(null=True)

    service: fields.ForeignKeyNullableRelation["Service"] = fields.ForeignKeyField(
        "models.Service",
        "proxies",
        on_delete=fields.SET_NULL,
        null=True,
    )
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User",
        "proxies",
        on_delete=fields.CASCADE,
        null=False,
    )
    server: fields.ForeignKeyRelation["Server"] = fields.ForeignKeyField(
        "models.Server",
        "proxies",
        on_delete=fields.CASCADE,
        null=False,
    )

    @property
    def display_name(self):
        if self.custom_name:
            return f"{self.username} ({self.custom_name})"

        if self.service:
            return f"{self.service.name} ({self.username})"
        return f"({self.username})"
