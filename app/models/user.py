from enum import IntEnum
from typing import TYPE_CHECKING

from tortoise import fields
from tortoise.expressions import Subquery
from tortoise.functions import Sum

from . import TimedBase

if TYPE_CHECKING:
    from .proxy import Proxy
    from .service import Service


class User(TimedBase):
    class Meta:
        table = "users"

    id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=200, null=True)
    name = fields.CharField(max_length=200, null=True)
    is_blocked = fields.BooleanField(default=False)

    super_user = fields.BooleanField(default=False)

    force_join_check = fields.DatetimeField(null=True)

    proxies: fields.ReverseRelation["Proxy"]
    invoices: fields.ReverseRelation["Invoice"]
    transactions: fields.ReverseRelation["Transaction"]
    purchased_services: fields.ManyToManyRelation["Service"]

    async def get_balance(self) -> int:
        q = (  # query to fetch sum of transactions and invoices amount of user
            await self.transactions.filter(status=Transaction.Status.finished)
            .annotate(trx_sum=Sum("amount"))
            .annotate(
                inv_sum=Subquery(
                    self.invoices.filter()
                    .annotate(inv=Sum("amount"))
                    .all()
                    .values_list("inv", flat=True)
                )
            )
            .all()
            .values("trx_sum", "inv_sum")
        )[0]

        return (q.get("trx_sum") or 0) - (q.get("inv_sum") or 0)


class Invoice(TimedBase):
    class Meta:
        table = "invoices"

    class Type(IntEnum):
        purchase = 1
        renew = 2

    id = fields.IntField(pk=True)
    amount = fields.IntField(null=False)
    type = fields.IntEnumField(Type, default=Type.purchase)
    proxy: fields.ForeignKeyNullableRelation["Proxy"] = fields.ForeignKeyField(
        "models.Proxy",
        "invoices",
        on_delete=fields.SET_NULL,
        null=True,
    )
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        "invoices",
        on_delete=fields.CASCADE,
    )
    transaction: fields.ForeignKeyNullableRelation[
        "Transaction"
    ] = fields.ForeignKeyField(
        "models.Transaction",
        "invoices",
        on_delete=fields.SET_NULL,
        null=True,
    )


class Transaction(TimedBase):
    class Meta:
        table = "transactions"

    class PaymentType(IntEnum):
        crypto = 1
        by_admin = 2

    class Status(IntEnum):
        waiting = 1
        failed = 2
        canceled = 3
        partially_paid = 4
        finished = 5

    id = fields.BigIntField(pk=True)
    type = fields.IntEnumField(PaymentType, null=False)
    status = fields.IntEnumField(Status, default=Status.waiting)

    finished_at = fields.DatetimeField(null=True)
    amount = fields.IntField(null=False)
    amount_paid = fields.IntField(null=True)

    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User",
        "transactions",
        on_delete=fields.CASCADE,
        null=False,
    )
    crypto_payment: fields.ReverseRelation["CryptoPayment"]
    byadmin_payment: fields.ReverseRelation["ByAdminPayment"]


class CryptoPayment(TimedBase):
    class Meta:
        table = "crypto_payments"

    class PaymentStatus(IntEnum):
        waiting = 0
        confirming = 1
        confirmed = 2
        sending = 3
        partially_paid = 4
        finished = 5
        failed = 6
        refunded = 7
        expired = 8

    type = fields.IntEnumField(
        Transaction.PaymentType, default=Transaction.PaymentType.crypto
    )
    usdt_rate = fields.IntField()
    invoice_id = fields.CharField(max_length=64)
    order_id = fields.CharField(max_length=64, null=True)
    price_amount = fields.FloatField()
    price_currency = fields.CharField(max_length=20)
    nowpm_created_at = fields.DatetimeField(null=True)

    pay_currency = fields.CharField(max_length=32, null=True)
    pay_amount = fields.FloatField(null=True)
    order_description = fields.CharField(max_length=64, null=True)
    nowpm_updated_at = fields.DatetimeField(null=True)
    payment_status = fields.IntEnumField(PaymentStatus, default=PaymentStatus.waiting)
    outcome_amount = fields.FloatField(null=True)
    outcome_currency = fields.CharField(max_length=20, null=True)
    purchase_id = fields.CharField(max_length=64, null=True)
    pay_address = fields.CharField(max_length=128, null=True)

    transaction: fields.OneToOneRelation[Transaction] = fields.OneToOneField(
        "models.Transaction",
        "crypto_payment",
        on_delete=fields.CASCADE,
        null=False,
    )


class ByAdminPayment(TimedBase):
    class Meta:
        table = "byadmin_payments"

    type = fields.IntEnumField(
        Transaction.PaymentType, default=Transaction.PaymentType.by_admin
    )
    by_admin: fields.ForeignKeyNullableRelation[User] = fields.ForeignKeyField(
        "models.User",
        "balance_transactions",
        on_delete=fields.SET_NULL,
        null=True,
    )

    transaction: fields.OneToOneRelation[Transaction] = fields.OneToOneField(
        "models.Transaction",
        "byadmin_payment",
        on_delete=fields.CASCADE,
        null=False,
    )
