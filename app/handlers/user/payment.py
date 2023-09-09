import uuid

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from tortoise.transactions import in_transaction

import config
from app.keyboards.base import CancelUserForm, MainMenu
from app.keyboards.user.account import UserPanel, UserPanelAction
from app.keyboards.user.payment import (
    ChargeMethods,
    ChargePanel,
    PayCryptoUrl,
    SelectPayAmount,
)
from app.models.user import CryptoPayment, Transaction, User
from app.utils.filters import IsJoinedToChannel
from app.utils.settings import Settings
from payment_clients.nobitex import CouldNotGetUSDTPrice, NobitexMarketAPI
from payment_clients.nowpayments import NowPaymentsAPI, NowPaymentsError

from . import router


class SelectCustomAmountForm(StatesGroup):
    method = State()
    amount = State()


@router.message(
    (F.text == MainMenu.back) | (F.text == MainMenu.cancel),
    StateFilter(SelectCustomAmountForm),
)
@router.message(F.text == MainMenu.charge, IsJoinedToChannel())
@router.callback_query(UserPanel.Callback.filter(F.action == UserPanelAction.charge))
async def charge(qmsg: Message | CallbackQuery, user: User, state: FSMContext = None):
    if (state is not None) and (await state.get_state() is not None):
        text = "🌀 عملیات لغو شد!"
        await state.clear()
        if isinstance(qmsg, CallbackQuery):
            await qmsg.answer(text)
        else:
            await qmsg.answer(text=text, reply_markup=ReplyKeyboardRemove())
    settings = await Settings.payment_settings()
    if not any([True for v in settings.values() if v]):
        text = """
در حال حاضر درگاه پرداخت غیرفعال می‌باشد! برای شارژ حساب با مدیر سیستم تماس بگیرید.
"""
        if isinstance(qmsg, Message):
            return await qmsg.answer(text)
        return await qmsg.message.edit_text(text)
    else:
        text = """
    ♻️ شما میتونید به روش‌های مختلفی حسابتون رو شارژ کنید🙄

    ✔️ حداقل میزان پرداختی برای شارژ حساب 20,000 تومان می‌باشد

    برای ادامه مراحل شارژ حساب، یکی از روش‌های پرداخت زیر رو انتخاب کنید👇
        """
        if isinstance(qmsg, Message):
            return await qmsg.answer(
                text, reply_markup=ChargePanel(settings).as_markup()
            )
        return await qmsg.message.edit_text(
            text, reply_markup=ChargePanel(settings).as_markup()
        )


@router.callback_query(ChargePanel.Callback.filter(F.method == ChargeMethods.crypto))
async def crypto_select_amount(query: CallbackQuery, user: User):
    try:
        if not await Settings.payment_crypto() or not await NowPaymentsAPI.status():
            return await query.answer(
                "📍 درحال حاضر امکان پرداخت ارز دیجیتال وجود ندارد! لطفا با پشتیبانی تماس بگیرید.",
                show_alert=True,
            )
    except NowPaymentsError as exc:
        await query.answer(
            "📍 درحال حاضر امکان پرداخت ارز دیجیتال وجود ندارد! لطفا با پشتیبانی تماس بگیرید.",
            show_alert=True,
        )
        raise exc

    # fmt: off
    text = f"""
✔️ شما در حال افزایش اعتبار با ارز دیجیتال هستید!

❗️اگر اشتباه وارد این بخش شدید دکمه «برگشت» را کلیک کنید
{config.CRYPTO_PAYMENT_HELP}
{config.FREE_CREDIT_ON_TEXT}

✔️ برای ادامه، مبلغ مورد نظر برای افزایش اعتبار رو انتخاب کنید:
‌‌
    """
    # fmt: on
    await query.message.edit_text(
        text, reply_markup=SelectPayAmount(method=ChargeMethods.crypto).as_markup()
    )


@router.callback_query(SelectPayAmount.Callback.filter(F.amount == 0))
async def enter_custom_amount(
    query: CallbackQuery,
    user: User,
    callback_data: SelectPayAmount.Callback,
    state: FSMContext,
):
    text = """
💴 مبلغ مورد نظر برای افزایش اعتبار را وارد کنید:
"""
    await state.set_state(SelectCustomAmountForm.amount)
    await state.set_data({"method": callback_data.method})
    await query.message.answer(
        text,
        reply_markup=CancelUserForm(cancel=True).as_markup(
            resize_keyboard=True, one_time_keyboard=True
        ),
    )


@router.message(SelectCustomAmountForm.amount)
async def get_custom_amount(message: Message, user: User, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError:
        return await message.reply("❌ لطفا مقداری عددی وارد کنید:")

    if amount < 20000:
        return await message.reply(f"❌ لطفا مقداری بیشتر از 20000 وارد کنید:")

    method = (await state.get_data()).get("method")
    free = (
        0
        if (not config.PAYMENTS_DISCOUNT_ON) or (amount < config.PAYMENTS_DISCOUNT_ON)
        else amount * (config.PAYMENTS_DISCOUNT_ON_PERCENT / 100)
    )
    callback_data = SelectPayAmount.Callback(amount=amount, free=free, method=method)
    if method == ChargeMethods.crypto:
        return await crypto_select_amount(message, user, callback_data=callback_data)


@router.callback_query(
    SelectPayAmount.Callback.filter(F.method == ChargeMethods.crypto)
)
async def crypto_select_amount(
    qmsg: CallbackQuery | Message, user: User, callback_data: SelectPayAmount.Callback
):
    if not await Settings.payment_crypto():
        if isinstance(qmsg, CallbackQuery):
            return await qmsg.answer(
                "📍 درحال حاضر امکان پرداخت ارز دیجیتال وجود ندارد! لطفا با پشتیبانی تماس بگیرید.",
                show_alert=True,
            )
        return await qmsg.answer(
            "📍 درحال حاضر امکان پرداخت ارز دیجیتال وجود ندارد! لطفا با پشتیبانی تماس بگیرید.",
            show_alert=True,
        )
    try:
        async with in_transaction():
            usdt_rate = await NobitexMarketAPI.get_price()
            transaction = await Transaction.create(
                type=Transaction.PaymentType.crypto,
                status=Transaction.Status.waiting,
                amount=callback_data.amount + callback_data.free,
                amount_free_given=callback_data.free,
                user=user,
            )
            invoice = await NowPaymentsAPI.create_invoice(
                price_amount=round(callback_data.amount / usdt_rate, 3),
                order_id=transaction.id,
            )
            await CryptoPayment.create(
                transaction=transaction,
                usdt_rate=usdt_rate,
                invoice_id=invoice.id,
                order_id=invoice.order_id,
                price_amount=invoice.price_amount,
                price_currency=invoice.price_currency,
                nowpm_created_at=invoice.created_at,
                nowpm_updated_at=invoice.updated_at,
            )
        text = f"""
✅ فاکتور افزایش اعتبار شما ساخته شد!

💳 شماره فاکتور: {transaction.id}
💲مبلغ قابل پرداخت: <b>{transaction.amount - transaction.amount_free_given:,}</b> تومان (<b>{invoice.price_amount}</b> دلار)
~~~~~~~~~~~~~~~~~~~~~~~~
🔵 تأیید پرداخت به صورت کاملاً خودکار انجام می‌شود. بعد از پرداخت و تأیید تراکنش در بلاکچین، مبلغ مورد نظر به حساب شما اضافه می‌شود!

⚠️ فاکتور پرداخت شما تا ۲ ساعت دیگر معتبر می‌باشد.

🟩 برای پرداخت روی دکمه زیر کلیک کنید:
‌‌
"""
        if isinstance(qmsg, CallbackQuery):
            return await qmsg.message.edit_text(
                text=text,
                reply_markup=PayCryptoUrl(url=invoice.invoice_url).as_markup(),
            )
        return await qmsg.answer(
            text=text, reply_markup=PayCryptoUrl(url=invoice.invoice_url).as_markup()
        )
    except NowPaymentsError as err:
        if isinstance(qmsg, CallbackQuery):
            await qmsg.answer(
                "📍 درحال حاضر امکان پرداخت ارز دیجیتال وجود ندارد! لطفا با پشتیبانی تماس بگیرید.",
                show_alert=True,
            )
        else:
            await qmsg.answer(
                "📍 درحال حاضر امکان پرداخت ارز دیجیتال وجود ندارد! لطفا با پشتیبانی تماس بگیرید."
            )
        raise err
    except CouldNotGetUSDTPrice as err:
        if isinstance(qmsg, CallbackQuery):
            await qmsg.answer(
                "📍 خطایی در دریافت نرخ ارز رخ داد! لطفا با پشتیبانی تماس بگیرید.",
                show_alert=True,
            )
        else:
            await qmsg.answer(
                "📍 خطایی در دریافت نرخ ارز رخ داد! لطفا با پشتیبانی تماس بگیرید."
            )
        raise err
