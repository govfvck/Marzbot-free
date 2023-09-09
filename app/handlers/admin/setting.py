from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.keyboards.admin.admin import AdminPanel, AdminPanelAction, CancelFormAdmin
from app.keyboards.admin.setting import (
    ConfirmSettings,
    SettingsActions,
    SettingsKeyboard,
)
from app.models.user import User
from app.utils.filters import SuperUserAccess
from app.utils.settings import Settings

from . import router

cancel_form = CancelFormAdmin().as_markup(resize_keyboard=True, one_time_only=True)


# @router.message(F.text.casefold() == "cancel", IsSuperUser(), StateFilter(AddCardForm))
# @router.message(Command("cancel"), IsSuperUser(), StateFilter(AddCardForm))
@router.callback_query(
    AdminPanel.Callback.filter(F.action == AdminPanelAction.settings), SuperUserAccess()
)
async def show_settings(
    query: CallbackQuery | Message, user: User, state: FSMContext | None = None
):
    if (state is not None) and (await state.get_state() is not None):
        await state.clear()
        await query.answer(text="Canceled!", reply_markup=ReplyKeyboardRemove())

    reply_markup = SettingsKeyboard(settings=await Settings.settings()).as_markup()
    if isinstance(query, CallbackQuery):
        return await query.message.edit_text("Settings:", reply_markup=reply_markup)
    return await query.answer("Settings:", reply_markup=reply_markup)


@router.callback_query(
    SettingsKeyboard.Callback.filter(F.action == SettingsActions.flip_access_only),
    SuperUserAccess(),
)
async def edit_settings(
    query: CallbackQuery, user: User, callback_data: SettingsKeyboard.Callback
):
    status = await Settings.bot_access_only()
    if not callback_data.confirmed:
        await query.answer()
        if not status:
            text = """
Confirm activating access only mode: 

❗️❗️<strong>be careful, if you do this only verified new users can use the bot.</strong>
            """
        else:
            text = """
Confirm disabling access only mode: 

❗️❗️<strong>be careful, every new user can use the bot.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmSettings(
                action=SettingsActions.flip_access_only,
            ).as_markup(),
        )
    if status:
        await Settings.set_bot_access_only(False)
        text = "access only disabled!"
    else:
        await Settings.set_bot_access_only(True)
        text = "access only enabled!"
    await query.answer(text, show_alert=True)
    await show_settings(
        query,
        user,
    )


@router.callback_query(
    SettingsKeyboard.Callback.filter(F.action == SettingsActions.flip_referral_system),
    SuperUserAccess(),
)
async def edit_settings(
    query: CallbackQuery, user: User, callback_data: SettingsKeyboard.Callback
):
    status = await Settings.bot_referral_system()
    if not callback_data.confirmed:
        await query.answer()
        if not status:
            text = """
Confirm activating referral system: 

❗️❗️<strong>be careful, if you do this users referral section will be disabled in bot.</strong>
            """
        else:
            text = """
Confirm disabling referral system: 

❗️❗️<strong>be careful, if you do this referral section will be enabled in bot.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmSettings(
                action=SettingsActions.flip_referral_system,
            ).as_markup(),
        )
    if status:
        await Settings.set_bot_referral_system(False)
        text = "referral system disabled!"
    else:
        await Settings.set_bot_referral_system(True)
        text = "referral system enabled!"
    await query.answer(text, show_alert=True)
    await show_settings(
        query,
        user,
    )


# payment methods statuses
@router.callback_query(
    SettingsKeyboard.Callback.filter(F.action == SettingsActions.flip_payment_crypto),
    SuperUserAccess(),
)
async def edit_settings(
    query: CallbackQuery, user: User, callback_data: SettingsKeyboard.Callback
):
    status = await Settings.payment_crypto()
    if not callback_data.confirmed:
        await query.answer()
        if not status:
            text = """
Confirm activating crypto payment: 

❗️❗️<strong>be careful, if you do this crypto payment button will be hidden.</strong>
            """
        else:
            text = """
Confirm disabling crypto payment: 

❗️❗️<strong>be careful, if you do this crypto payment button will be visible.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmSettings(
                action=SettingsActions.flip_payment_crypto,
            ).as_markup(),
        )
    if status:
        await Settings.set_payment_crypto(False)
        text = "crypto payment disabled!"
    else:
        await Settings.set_payment_crypto(True)
        text = "crypto payment enabled!"
    await query.answer(text, show_alert=True)
    await show_settings(
        query,
        user,
    )


@router.callback_query(
    SettingsKeyboard.Callback.filter(
        F.action == SettingsActions.flip_payment_card_to_card
    ),
    SuperUserAccess(),
)
async def edit_settings(
    query: CallbackQuery, user: User, callback_data: SettingsKeyboard.Callback
):
    status = await Settings.payment_card_to_card()
    if not callback_data.confirmed:
        await query.answer()
        if not status:
            text = """
Confirm activating card_to_card payment: 

❗️❗️<strong>be careful, if you do this card to card payment button will be hidden.</strong>
            """
        else:
            text = """
Confirm disabling card to card payment: 

❗️❗️<strong>be careful, if you do this card to card payment button will be visible.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmSettings(
                action=SettingsActions.flip_payment_card_to_card,
            ).as_markup(),
        )
    if status:
        await Settings.set_payment_card_to_card(False)
        text = "card to card payment disabled!"
    else:
        await Settings.set_payment_card_to_card(True)
        text = "card to card payment enabled!"
    await query.answer(text, show_alert=True)
    await show_settings(
        query,
        user,
    )


@router.callback_query(
    SettingsKeyboard.Callback.filter(
        F.action == SettingsActions.flip_payment_rial_gateway
    ),
    SuperUserAccess(),
)
async def edit_settings(
    query: CallbackQuery, user: User, callback_data: SettingsKeyboard.Callback
):
    status = await Settings.payment_rial_gateway()
    if not callback_data.confirmed:
        await query.answer()
        if not status:
            text = """
Confirm activating rial gateway payment: 

❗️❗️<strong>be careful, if you do this rial gateway payment button will be hidden.</strong>
            """
        else:
            text = """
Confirm disabling rial gateway payment: 

❗️❗️<strong>be careful, if you do this rial gateway payment button will be visible.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmSettings(
                action=SettingsActions.flip_payment_rial_gateway,
            ).as_markup(),
        )
    if status:
        await Settings.set_payment_rial_gateway(False)
        text = "rial gateway payment disabled!"
    else:
        await Settings.set_payment_rial_gateway(True)
        text = "rial gateway payment enabled!"
    await query.answer(text, show_alert=True)
    await show_settings(
        query,
        user,
    )


@router.callback_query(
    SettingsKeyboard.Callback.filter(
        F.action == SettingsActions.flip_payment_perfect_money
    ),
    SuperUserAccess(),
)
async def edit_settings(
    query: CallbackQuery, user: User, callback_data: SettingsKeyboard.Callback
):
    status = await Settings.payment_perfect_money()
    if not callback_data.confirmed:
        await query.answer()
        if not status:
            text = """
Confirm activating perfect money payment: 

❗️❗️<strong>be careful, if you do this perfect money payment button will be hidden.</strong>
            """
        else:
            text = """
Confirm disabling perfect money payment: 

❗️❗️<strong>be careful, if you do this perfect money payment button will be visible.</strong>
            """
        return await query.message.edit_text(
            text,
            reply_markup=ConfirmSettings(
                action=SettingsActions.flip_payment_perfect_money,
            ).as_markup(),
        )
    if status:
        await Settings.set_payment_perfect_money(False)
        text = "perfect money payment disabled!"
    else:
        await Settings.set_payment_perfect_money(True)
        text = "perfect money payment enabled!"
    await query.answer(text, show_alert=True)
    await show_settings(
        query,
        user,
    )
