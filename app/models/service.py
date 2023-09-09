from enum import Enum
from typing import TYPE_CHECKING

from tortoise import fields

from app.models import TimedBase

if TYPE_CHECKING:
    from .server import Server
    from .user import User


class Service(TimedBase):
    class Meta:
        table = "services"

    class ServiceProxyFlow(str, Enum):
        none = None
        xtls_rprx_vision = "xtls-rprx-vision"

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, null=False)
    data_limit = fields.BigIntField(null=False)  # in bytes
    expire_duration = fields.IntField(null=False)  # in seconds
    inbounds = fields.JSONField(null=False)
    flow = fields.CharEnumField(
        ServiceProxyFlow, max_length=20, null=True, default=ServiceProxyFlow.none
    )
    price = fields.IntField(null=False)  # in Tomans

    one_time_only = fields.BooleanField(
        default=False
    )  # each user can only buy this once
    is_test_service = fields.BooleanField(
        default=False,  # normal users can get it only once, resellers can get it for config.DEFAULT_DAILY_TEST_SERVICES or user.setting.daily_test_services
    )

    purchaseable = fields.BooleanField(default=False)
    renewable = fields.BooleanField(default=False)

    server: fields.ForeignKeyRelation["Server"] = fields.ForeignKeyField(
        "models.Server",
        "services",
        on_delete=fields.CASCADE,
        null=False,
    )

    purchased_by: fields.ManyToManyRelation["User"] = fields.ManyToManyField(
        "models.User",
        through="user_purchased",
        related_name="purchased_services",
    )

    @property
    def display_name(self):
        if not self.price:
            return self.name
        return f"{self.name} | {self.price:,} تومان"

    def get_price(self) -> int:
        return self.price

    def create_proxy_protocols(self, protocol: str) -> dict[str, str]:
        if protocol == "vless" and self.flow is not None:
            return {"flow": self.flow}
        return {}
