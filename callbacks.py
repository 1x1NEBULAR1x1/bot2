import asyncio
import datetime
import random
import re

from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import keyboards as kb
from cfg import BOT_USERNAME, ADMINS_IDS, REFERRER_MISSION, END_GAME_MESSAGE, CHATS_IDS, MOMENT_LOTO, DAILY_LOTO, \
    WEEKLY_LOTO, MONTHLY_LOTO, MODERATORS_IDS, QUESTIONS, HELP, LOTO_TYPE, LOTO_LIMIT
from db import (get_last_game, delete_game, start_game, get_users, get_game, join_game, get_user_address,
                get_active_addresses_count, get_referrers_count, get_addresses, deactivate_address,
                activate_address, delete_address, get_address, get_prizes, check_subscribe_db, get_free_address,
                get_prizes_count, get_prize, del_prize, end_game, get_game_users, add_winner, get_user,
                get_active_game, number_of_users, get_game_winners, is_banned, update_balance, get_daily_ticket,
                get_monthly_ticket, get_weekly_ticket, get_daily_users_count, get_weekly_users_count,
                get_monthly_users_count, add_spin, check_vip, get_games_history, add_pin, get_pins,
                get_all_prizes, add_moment_loto, get_daily_moment_loto_by_user_id, get_weekly_moment_loto_by_user_id,
                get_monthly_moment_loto_by_user_id, get_daily_moment_loto, get_weekly_moment_loto,
                get_monthly_moment_loto, set_user_anonim, get_all_moment_loto, get_daily_moment_loto_db,
                get_weekly_moment_loto_db, get_monthly_moment_loto_db, update_username_name, get_sends, delete_button,
                get_send_button, delete_send, delete_send_media, add_send,
                get_chats, get_chat, delete_chat, get_scheduled_later, get_scheduled_interval, get_send,
                get_scheduled_send, delete_scheduled_send, deactivate_scheduled_send, activate_scheduled_send,
                get_users_vip, get_users_novip, get_users_no_admin, get_unread_messages_count, get_messages_from_user,
                get_unread_messages_from_user, get_messages_from_sender, get_message,
                delete_message, add_message_from_user, read_message, unread_message, add_donate, get_donates,
                get_time_limit, get_antispam, edit_antispam, get_request, edit_request, get_goodbye, edit_goodbye,
                get_game_timeout, set_game_timeout)
from fsm import FSM
from heandlers import is_chat_member, start, user_send_message, admin_send_message, interval_sending, later_sending, \
    is_moderator

callbacks = Router()
@callbacks.callback_query(F.data == 'moment_block')
async def moment_block(call: CallbackQuery):
    await call.answer('⚠  На вашем балансе недостаточно средств', cache_time=20)
@callbacks.callback_query(F.data == 'loto_block_1')
async def loto_block_1(call: CallbackQuery):
    await call.answer('⚠  На вашем балансе недостаточно средств', cache_time=20)
@callbacks.callback_query(F.data == 'loto_block_2')
async def loto_block_2(call: CallbackQuery):
    await call.answer('⚠  Необходимо сыграть минимум 10 игр в моментальную лотерею', cache_time=20)
@callbacks.callback_query(F.data.startswith('admin_timestart_scheduled_'))
async def admin_timestart_scheduled(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id, send_id=int(call.data.split('_')[3]))
    await call.message.edit_text('Введите время начала рассылки в формате ЧЧ:ММ',
                                 reply_markup=await kb.admin_back_to_interval_keyboard())
    await state.set_state(FSM.set_send_starttime)
@callbacks.callback_query(F.data.startswith('admin_timeend_scheduled_'))
async def admin_timeend_scheduled(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id, send_id=int(call.data.split('_')[3]))
    await call.message.edit_text('Введите время окончания рассылки в формате ЧЧ:ММ',
                                 reply_markup=await kb.admin_back_to_interval_keyboard())
    await state.set_state(FSM.set_send_endtime)
@callbacks.callback_query(F.data == 'admin_moment_min')
async def admin_moment_min(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите минимальную ставку',
                                 reply_markup=await kb.admin_back_to_loto_settings_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_moment_min)
@callbacks.callback_query(F.data == 'admin_moment_max')
async def admin_moment_max(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите максимальную ставку',
                                 reply_markup=await kb.admin_back_to_loto_settings_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_moment_max)
@callbacks.callback_query(F.data.startswith('captcha_'))
async def captcha(call: CallbackQuery, state: FSMContext, bot: Bot):
    check = int(call.data.split('_')[1])
    if check == 1:
        await start(message=call.message, bot=bot, state=state, captcha_check=True)
    else:
        await start(message=call.message, bot=bot, state=state, captcha_check=False)
@callbacks.callback_query(F.data == 'user_help')
async def user_help(call: CallbackQuery):
    await call.message.edit_text('🙋‍♂️  <b>Помощ и поддержка</b>', reply_markup=await kb.user_help_keyboard())
@callbacks.callback_query(F.data == 'user_contact')
async def user_contact(call: CallbackQuery):
    await call.message.edit_text('📞  <b>Связь с администором</b>', reply_markup=await kb.admin_url_keyboard())
@callbacks.callback_query(F.data == 'user_questions')
async def user_questions(call: CallbackQuery):
    text = '📚  <b>Вопросы и ответы</b>\n'
    for question in QUESTIONS:
        text += f'❓  <b><i>{question[0]}</i> - ✅  {question[1]}\n</b>'
    await call.message.edit_text(text, reply_markup=await kb.back_to_help_keyboard())
@callbacks.callback_query(F.data == 'user_use')
async def user_use(call: CallbackQuery):
    await call.message.edit_text(HELP, reply_markup=await kb.back_to_help_keyboard())
@callbacks.callback_query(F.data == 'admin_request')
async def admin_request(call: CallbackQuery):
    value, text = 0, 'Ошибочное значение'
    if await get_request():
        if (await get_request())[0] == 1:
            text = 'Бот принимает запросы на вступление в чаты'
            value = 1
        else:
            text = 'Бот не принимает запросы на вступление в чаты'
            value = 0
    await call.message.edit_text(text, reply_markup=await kb.admin_request_keyboard(value))
@callbacks.callback_query(F.data == 'admin_request_on')
async def admin_request_on(call: CallbackQuery):
    await edit_request(1)
    await call.message.edit_text('Бот принимает запросы на вступление в чаты',
                                 reply_markup=await kb.admin_request_keyboard(1))
@callbacks.callback_query(F.data == 'admin_request_off')
async def admin_request_off(call: CallbackQuery):
    await edit_request(0)
    await call.message.edit_text('Бот не принимает запросы на вступление в чаты',
                                 reply_markup=await kb.admin_request_keyboard(0))
@callbacks.callback_query(F.data == 'admin_goodbye')
async def admin_goodbye(call: CallbackQuery):
    value, text = 0, 'Прощание не включено'
    if await get_goodbye():
        if (await get_goodbye())[0] == 1:
            text = 'Прощальное сообщение включено'
            value = 1
        else:
            text = 'Прощальное сообщение выключено'
            value = 0
    await call.message.edit_text(text, reply_markup=await kb.admin_goodbye_keyboard(value))
@callbacks.callback_query(F.data == 'admin_goodbye_on')
async def admin_goodbye_on(call: CallbackQuery):
    await edit_goodbye(1)
    await call.message.edit_text('Прощание включено', reply_markup=await kb.admin_goodbye_keyboard(1))
@callbacks.callback_query(F.data == 'admin_goodbye_off')
async def admin_goodbye_off(call: CallbackQuery):
    await edit_goodbye(0)
    await call.message.edit_text('Прощание выключено', reply_markup=await kb.admin_goodbye_keyboard(0))
@callbacks.callback_query(F.data == 'admin_accept_message')
async def admin_accept_message(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if not data:
        await call.message.answer('Произошла ошибка в форме', reply_markup=await kb.admin_back_keyboard())
        return
    msg = await add_message_from_user(data["user_id"], data["sender_id"], data["text"])
    await bot.send_message(chat_id=data["user_id"], text=data["text"],
                           reply_markup=await kb.user_message_keyboard(msg))
    await bot.edit_message_text(text='Сообщение отправлено!', message_id=data["message_id"], 
                                chat_id=call.message.chat.id, reply_markup=await kb.admin_message_keyboard(msg[0]))
@callbacks.callback_query(F.data == 'admin_messages_send')
async def admin_messaged_send(call: CallbackQuery, state: FSMContext):
    await state.update_data(sender_id=call.message.chat.id, message_id=call.message.message_id)
    await call.message.edit_text('Введите юзернейм пользователя',
                                 reply_markup=await kb.admin_back_to_messages_keyboard())
    await state.set_state(FSM.set_message_user)
@callbacks.callback_query(F.data == 'user_mail')
async def user_mail(call: CallbackQuery):
    unread_count = await get_unread_messages_count(call.message.chat.id)
    await call.message.edit_text('📬<b>  Почта:</b>', reply_markup=await kb.user_mail_keyboard(unread_count))
@callbacks.callback_query(F.data == 'user_messages_post')
async def user_messages_post(call: CallbackQuery):
    messages = await get_messages_from_user(call.message.chat.id)
    unread_messages = await get_unread_messages_from_user(call.message.chat.id)
    await call.message.edit_text('📬 <b> Сообщения:</b>',
                                 reply_markup=await kb.user_messages_post_keyboard(messages, unread_messages,
                                                                                   call.message.chat.id))
@callbacks.callback_query(F.data.startswith('user_messages_send'))
async def user_messages_send(call: CallbackQuery):
    await call.message.edit_text('📍 <b> Выберите администратора, для отправки сообщения:</b>',
                                 reply_markup=await kb.user_messages_send_keyboard(ADMINS_IDS))
@callbacks.callback_query(F.data.startswith('user_messages_to_'))
async def user_messages_to(call: CallbackQuery, state: FSMContext):
    admin_id = int(call.data.split('_')[3])
    await state.update_data(admin_id=admin_id, sender_id=call.message.chat.id, message_id=call.message.message_id)
    await call.message.edit_text('✏ <b> Введите текст сообщения:</b>',
                                 reply_markup=await kb.user_back_to_messages_keyboard())
    await state.set_state(FSM.set_user_message_text)
@callbacks.callback_query(F.data == 'user_accept_message')
async def user_accept_message(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if not data:
        await call.message.answer('Произошла ошибка в форме', reply_markup=await kb.user_back_keyboard())
        return
    user = await get_user(data['sender_id'])
    msg = await add_message_from_user(data['sender_id'], data['admin_id'], data['text'])
    await bot.send_message(chat_id=data['admin_id'], text=f'💬<b>  Сообщение от пользователя '
                                                          f'{user[1] if user[1] else user[2]}:\n{data["text"]}</b>',
                           reply_markup=await kb.admin_message_keyboard(msg[0]))
    await bot.edit_message_text('✅ <b> Сообщение отправлено</b>',
                                reply_markup=await kb.user_back_to_messages_keyboard(),
                                chat_id=call.message.chat.id, message_id=data['message_id'])
    await state.clear()
@callbacks.callback_query(F.data == 'user_accept_reply_message')
async def user_accept_reply_message(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    admin_text = (await get_message(data['msg_id']))[4][:20:]
    await bot.send_message(chat_id=data['user_id'], text=f'💬<b>  Ответ от пользователя на сообщение {admin_text}:'
                                                         f'\n{data["text"]}</b>',
                           reply_markup=await kb.admin_message_keyboard(data["msg_id"]))
    await add_message_from_user(data['user_id'], data['sender_id'], data['text'])
    await bot.edit_message_text('✅ <b> Ответ отправлен</b>',
                                reply_markup=await kb.user_back_to_messages_keyboard(),
                                chat_id=call.message.chat.id, message_id=data['message_id'])
    await state.clear()
@callbacks.callback_query(F.data.startswith('user_messages_from_'))
async def user_messages_from(call: CallbackQuery):
    sender = int(call.data.split('_')[3])
    messages = await get_messages_from_sender(call.message.chat.id, sender)
    await call.message.edit_text('📬<b>  Сообщения:</b>',
                                 reply_markup=await kb.user_messages_from_keyboard(messages))

@callbacks.callback_query(F.data.startswith('user_reply_message_'))
async def user_reply_message(call: CallbackQuery, state: FSMContext):
    message_id = int(call.data.split('_')[3])
    message = await get_message(message_id)
    await state.update_data(msg_id=message_id, user_id=message[2], sender_id=call.message.chat.id,
                            message_id=call.message.message_id)
    await call.message.edit_text('✏ <b> Введите текст ответа:</b>',
                                 reply_markup=await kb.user_back_to_messages_keyboard())
    await state.set_state(FSM.set_user_reply_text)
@callbacks.callback_query(F.data == 'admin_messages')
async def admin_messages(call: CallbackQuery):
    messages_count = await get_unread_messages_count(call.message.chat.id)
    await call.message.edit_text('Меню сообщений:',
                                 reply_markup=await kb.admin_messages_keyboard(messages_count))
@callbacks.callback_query(F.data == 'admin_messages_post')
async def admin_messages_post(call: CallbackQuery):
    messages = await get_messages_from_user(call.message.chat.id)
    unread_messages = await get_unread_messages_from_user(call.message.chat.id)
    await call.message.edit_text('Меню сообщений:',
                                 reply_markup=await kb.admin_messages_post_keyboard(messages, unread_messages,
                                                                                    call.message.chat.id))
@callbacks.callback_query(F.data.startswith('admin_messages_from_'))
async def admin_messages_from(call: CallbackQuery):
    sender = int(call.data.split('_')[3])
    messages = await get_messages_from_sender(call.message.chat.id, sender)
    await call.message.edit_text('Меню сообщений:',
                                 reply_markup=await kb.admin_messages_from_keyboard(messages))
@callbacks.callback_query(F.data.startswith('admin_message_'))
async def admin_message(call: CallbackQuery):
    message_id = int(call.data.split('_')[2])
    message = await get_message(message_id)
    user = await get_user(message[2])
    await read_message(message_id)
    await call.message.edit_text(f'Сообщение от {user[1] if user[1] else user[2]}:\n{message[4]}',
                                 reply_markup=await kb.admin_message_keyboard(message_id))
@callbacks.callback_query(F.data.startswith('admin_delete_message_'))
async def admin_delete_message(call: CallbackQuery):
    message_id = int(call.data.split('_')[3])
    await call.message.edit_text('Подтвердить удаление',
                                 reply_markup=await kb.admin_accept_delete_message_keyboard(message_id))
@callbacks.callback_query(F.data.startswith('admin_accept_delete_message_'))
async def admin_accept_delete_message(call: CallbackQuery):
    message_id = int(call.data.split('_')[4])
    await delete_message(message_id)
    await call.message.edit_text('Сообщение удалено', reply_markup=await kb.admin_back_to_messages_keyboard())
@callbacks.callback_query(F.data.startswith('admin_answer_message_'))
async def admin_answer_message(call: CallbackQuery, state: FSMContext):
    message_id = int(call.data.split('_')[3])
    user = await get_user((await get_message(message_id))[1])
    await state.update_data(message_id=call.message.message_id, user_id=user[0], sender_id=call.message.chat.id,
                            msg_id=message_id)
    await call.message.edit_text(f'Введите ответ для {user[1] if user[1] else user[2]}:',
                                 reply_markup=await kb.admin_back_to_messages_keyboard())
    await state.set_state(FSM.set_answer_text)
@callbacks.callback_query(F.data == 'admin_send_answer')
async def admin_send_answer(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg = await get_message(data["msg_id"])
    await bot.send_message(chat_id=msg[1], text=f'<b>💬  Ответ от администратора на сообщение: </b>\n'
                                                         f'<i>{msg[4][:20:]}\n</i>'
                                                         f'<b>{data["text"]}</b>',
                           reply_markup=await kb.user_answer_keyboard(msg[2]))
    await add_message_from_user(data['user_id'], data['sender_id'], data['text'])
    await bot.edit_message_text(text='Ответ отправлен', message_id=data['message_id'], chat_id=call.message.chat.id,
                                reply_markup=await kb.admin_back_to_messages_keyboard())
    await state.clear()
@callbacks.callback_query(F.data.startswith('admin_unread_message_'))
async def admin_unread_message(call: CallbackQuery):
    message_id = int(call.data.split('_')[3])
    await unread_message(message_id)
    await call.message.edit_text(f'Сообщение отмечено как непрочитанное',
                                 reply_markup=await kb.admin_back_to_messages_keyboard())
@callbacks.callback_query(F.data == 'admin_moderators')
async def admin_moderators(call: CallbackQuery):
    await call.message.edit_text('Меню модераторов:', reply_markup=await kb.admin_moderators_keyboard())
@callbacks.callback_query(F.data == 'admin_list_moderators')
async def admin_list_moderators(call: CallbackQuery):
    await call.message.edit_text('Список модераторов:',
                                 reply_markup=await kb.admin_list_moderators_keyboard(MODERATORS_IDS))
@callbacks.callback_query(F.data.startswith('admin_delete_moderator_'))
async def admin_delete_moderator(call: CallbackQuery):
    moderator_id = int(call.data.split('_')[3])
    await call.message.edit_text('Подтвердить удаление',
                                 reply_markup=await kb.admin_accept_delete_moderator_keyboard(moderator_id))
@callbacks.callback_query(F.data.startswith('admin_accept_delete_moderator_'))
async def admin_accept_delete_moderator(call: CallbackQuery):
    moderator_id = int(call.data.split('_')[4])
    MODERATORS_IDS.remove(moderator_id)
    await call.message.edit_text('Модератор удален', reply_markup=await kb.admin_moderators_keyboard())
@callbacks.callback_query(F.data.startswith('admin_moderator_'))
async def admin_moderator(call: CallbackQuery):
    moderator_id = int(call.data.split('_')[2])
    await call.message.edit_text('Меню модератора:',
                                 reply_markup=await kb.admin_moderator_keyboard(moderator_id))
@callbacks.callback_query(F.data == 'admin_add_moderator')
async def admin_add_moderator(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите username модератора (он должен быть зарегистрирован в боте):',
                                 reply_markup=await kb.admin_back_to_moderators_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_moderator_id)
@callbacks.callback_query(F.data == 'admin_accept_moderator')
async def admin_accept_moderator(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    MODERATORS_IDS.append(data['user_id'])
    await bot.edit_message_text('Модератор добавлен', reply_markup=await kb.admin_moderators_keyboard(),
                                chat_id=call.message.chat.id, message_id=data['message_id'])
    await state.clear()
@callbacks.callback_query(F.data.startswith('user_message_'))
async def user_message(call: CallbackQuery):
    message_id = int(call.data.split('_')[2])
    message = await get_message(message_id)
    await read_message(message_id)
    await call.message.edit_text(f'💬<b>  Сообщение:\n<i>{message[4]}</i></b>',
                                 reply_markup=await kb.user_message_keyboard(message))
@callbacks.callback_query(F.data == 'admin_settings')
async def admin_settings(call: CallbackQuery):
    await call.message.edit_text('Меню настроек:', reply_markup=await kb.admin_settings_keyboard())
@callbacks.callback_query(F.data == 'user_donate')
async def user_donate(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('💸  <b>Мы очень благодарны за вашу поддержку!\nЕсли у вас есть желание помочь '
                                'проекту, вы можете перевести любую сумму с баланса вашего аккаунта и поддержать нас!\n'
                                'Достаточно ввести сумму пожертвования</b>', reply_markup=await kb.user_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_value_donate)
@callbacks.callback_query(F.data == 'user_accept_donate')
async def user_accept_donate(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.edit_message_text('🙋‍♂️  <b>Мы очень благодарны за вашу поддержку!</b>', chat_id=call.message.chat.id,
                                message_id=data['message_id'], reply_markup=await kb.user_back_keyboard())
    await update_balance(call.message.chat.id, -data['value'])
    await add_donate(call.message.chat.id, data['value'])
@callbacks.callback_query(F.data == 'admin_donates')
async def admin_donates(call: CallbackQuery):
    donates, text, total = await get_donates(), '', 0
    for donate in donates:
        total += donate[2]
        user = await get_user(donate[1])
        text += f'{donate[2]} от {user[1] if user[1] else user[2]} ({donate[3]})\n'
    text += f'<b>Общая сумма пожертвований: {total}</b>'
    await call.message.edit_text('Пожертвования:\n' + text, reply_markup=await kb.admin_back_keyboard())
@callbacks.callback_query(F.data == 'admin_antispam')
async def admin_antispam(call: CallbackQuery):
    time_limit = await get_time_limit()
    antispam = await get_antispam()
    text = (f'Установленное ограничение обработки сообщений: {time_limit[0]} секунд на '
            f'обновление') if antispam[0] == 1 else 'Антиспам выключен'
    await call.message.edit_text(text=text, reply_markup=await kb.admin_antispam_keyboard(antispam))
@callbacks.callback_query(F.data == 'admin_antispam_on')
async def admin_antispam_on(call: CallbackQuery):
    time_limit = await get_time_limit()
    await edit_antispam(1)
    await call.message.edit_text(f'Антиспам включен\nУстановленное ограничение обработки сообщений: {time_limit[0]} '
                                 f'секунд на обновление',
                                 reply_markup=await kb.admin_antispam_keyboard((await get_antispam())[0]))
@callbacks.callback_query(F.data == 'admin_antispam_off')
async def admin_antispam_off(call: CallbackQuery):
    await edit_antispam(0)
    await call.message.edit_text('Антиспам выключен',
                                 reply_markup=await kb.admin_antispam_keyboard((await get_antispam())[0]))
@callbacks.callback_query(F.data == 'admin_antispam_edit')
async def admin_antispam_edit(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите время ограничения обработки сообщений в секундах:',
                                 reply_markup=await kb.admin_back_to_antispam_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_antispam_value)
@callbacks.callback_query(F.data.startswith('admin_later_'))
async def admin_later(call: CallbackQuery):
    page = int(call.data.split('_')[2])
    scheds = await get_scheduled_later()
    await call.message.edit_text(text='Меню отложенных сообщений:',
                                 reply_markup=await kb.admin_later_keyboard(scheds, page))
@callbacks.callback_query(F.data.startswith('admin_laterr_') or F.data.startswith('admin_interval_'))
async def admin_late_send(call: CallbackQuery):
    sched_id = int(call.data.split('_')[2])
    sched = await get_scheduled_send(sched_id)
    send = await get_send(sched[0])
    await call.message.edit_text(text=f'{send[1] if send[1] else "Медиа"} отправится в {sched[1]} в  {sched[3]}',
                                 reply_markup=await kb.admin_scheduled_keyboard(sched_id,
                                                                                call.data.split('_')[1] == 'interval'))
@callbacks.callback_query(F.data.startswith('admin_deactivate_scheduled_'))
async def admin_cancel_scheduled(call: CallbackQuery, scheduler: AsyncIOScheduler):
    sched_id = int(call.data.split('_')[3])
    await deactivate_scheduled_send(sched_id)
    try:
        scheduler.remove_job(job_id=str(sched_id))
    except:
        pass
    await call.message.edit_text(text='Отправка отменена', reply_markup=await kb.admin_back_to_sends_keyboard())
@callbacks.callback_query(F.data.startswith('admin_delete_scheduled_'))
async def admin_delete_scheduled(call: CallbackQuery, scheduler: AsyncIOScheduler):
    sched_id = int(call.data.split('_')[3])
    await delete_scheduled_send(sched_id)
    try: scheduler.remove_job(job_id=str(sched_id))
    except: pass
    await call.message.edit_text(text='Отправка удалена', reply_markup=await kb.admin_back_to_sends_keyboard())
@callbacks.callback_query(F.data.startswith('admin_activate_scheduled_'))
async def admin_activate_scheduled(call: CallbackQuery, scheduler: AsyncIOScheduler, bot: Bot):
    sched_id = int(call.data.split('_')[3])
    sched = await get_scheduled_send(sched_id)
    await activate_scheduled_send(sched_id)
    users = []
    match sched[1]:
        case "vip":
            users = await get_users_vip()
        case "novip":
            users = await get_users_novip()
        case "all":
            users = await get_users_no_admin(ADMINS_IDS)
        case "chat":
            users = await get_chats()
    if sched[2] == 'interval':
        try:
            match_ = re.match(r'(\d+)\s?([А-яA-z])', sched[3])
            interval = int(match_.group(1))
            match match_.group(2):
                case 'м':
                    interval *= 1
                case 'ч':
                    interval *= 60
                case 'д':
                    interval *= 60 * 24
                case 'н':
                    interval *= 60 * 24 * 7
                case '':
                    interval *= 60 * 24
        except ValueError:
            return
        scheduler.add_job(func=interval_sending, trigger='interval', minutes=interval, id=str(sched[4]),
                          kwargs={'users': users, 'send_id': sched[0], 'bot': bot})
        await call.message.edit_text(text='Отправка активирована',
                                     reply_markup=await kb.admin_back_to_interval_keyboard())
    else:
        scheduler.add_job(func=later_sending, trigger='date', run_date=datetime.datetime.fromisoformat(sched[3]),
                          id=f'{sched[4]}', kwargs={'users': users, 'send_id': sched[0], 'bot': bot, 'sched_id': sched[4]})
        await call.message.edit_text(text='Отправка активирована',
                                     reply_markup=await kb.admin_back_to_later_keyboard())
@callbacks.callback_query(F.data.startswith('admin_delete_chat_'))
async def admin_delete_chat(call: CallbackQuery):
    chat_id = int(call.data.split('_')[3])
    await call.message.edit_text(text='Подтвердить удаление',
                                 reply_markup=await kb.admin_accept_delete_chat_keyboard(chat_id))
@callbacks.callback_query(F.data.startswith('admin_accept_delete_chat_'))
async def admin_accept_delete_chat(call: CallbackQuery):
    chat_id = int(call.data.split('_')[4])
    await delete_chat(chat_id)
    await call.message.edit_text(text='Чат удален', reply_markup=await kb.admin_back_to_chats_keyboard())
@callbacks.callback_query(F.data.startswith('admin_intervals_'))
async def admin_interval(call: CallbackQuery):
    scheds = await get_scheduled_interval()
    page = int(call.data.split('_')[2])
    await call.message.edit_text(text='Меню интервальных сообщений:',
                                 reply_markup=await kb.admin_interval_keyboard(scheds, page))
@callbacks.callback_query(F.data.startswith('admin_intervall_'))
async def admin_interval_send(call: CallbackQuery):
    sched_id = int(call.data.split('_')[2])
    sched = await get_scheduled_send(sched_id)
    send = await get_send(sched[0])
    text = f'{send[1] if send[1] else "Медиа"} отправляется каждые {sched[3]}'
    if send[4]:
        text += f' с {send[4]}'
    if send[5]:
        text += f' до {send[5]}'
    await call.message.edit_text(text=text,
                                 reply_markup=await kb.admin_scheduled_keyboard(sched_id, True))
@callbacks.callback_query(F.data.startswith('admin_sends_all'))
async def admin_sends_all(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    page = int(call.data.split('_')[3])
    try:
        if data:
            if data['message_id_1']:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=data['message_id_1'])
                await state.clear()
    except TelegramBadRequest:
        pass
    await call.message.edit_text(text='Меню отправки сообщений:',
                                 reply_markup=await kb.admin_sends_all_keyboard(await get_sends(), page))
@callbacks.callback_query(F.data.startswith('admin_send_all_'))
async def admin_send_all(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[3])
    await call.message.delete()
    await state.update_data(message_id_1=
    (await user_send_message(bot=bot, user_id=call.message.chat.id, send_id=send_id)).message_id)
    await state.update_data(message_id_2=(await call.message.answer(text='Начать рассылку?',
                            reply_markup=await kb.admin_accept_send_all_keyboard(send_id))).message_id)
@callbacks.callback_query(F.data.startswith('admin_accept_send_all_'))
async def admin_accept_send_all(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    users = await get_users()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_1'])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_2'])
    msg = await call.message.answer(text=f'Рассылка начата, примерное время отправки: {len(users) * 0.05} секунд')
    for user in users:
        if user[0] != call.message.chat.id:
            await user_send_message(user_id=user[0], bot=bot, send_id=send_id)
    await bot.edit_message_text(text='Рассылка завершена', message_id=msg.message_id, chat_id=call.message.chat.id,
                                reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.clear()
@callbacks.callback_query(F.data.startswith('admin_sends_vip_'))
async def admin_sends_vip(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    page = int(call.data.split('_')[3])
    try:
        if data:
            if data['message_id_1']:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=data['message_id_1'])
                await state.clear()
    except:
        pass
    await call.message.edit_text(text='Меню отправки сообщений для VIP:',
                                 reply_markup=await kb.admin_sends_vip_keyboard(await get_sends(), page))
@callbacks.callback_query(F.data.startswith('admin_send_vip_'))
async def admin_send_vip(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[3])
    await call.message.delete()
    await state.update_data(message_id_1=(await user_send_message(bot=bot, user_id=call.message.chat.id,
                                                                  send_id=send_id)).message_id)
    await state.update_data(message_id_2=(await call.message.answer(text='Начать рассылку?',
                            reply_markup=await kb.admin_accept_send_vip_keyboard(send_id))).message_id)
@callbacks.callback_query(F.data.startswith('admin_accept_send_vip_'))
async def admin_accept_send_vip(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    users = await get_users()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_1'])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_2'])
    msg = await call.message.answer(text=f'Рассылка начата, примерное время отправки: {len(users) * 0.05} секунд')
    for user in users:
        if await check_vip(user[0]):
            if user[0] != call.message.chat.id:
                await user_send_message(user_id=user[0], bot=bot, send_id=send_id)
    await bot.edit_message_text(text='Рассылка завершена', message_id=msg.message_id,
                                reply_markup=await kb.admin_sends_vip_keyboard(await get_sends()),
                                chat_id=call.message.chat.id)
    await state.clear()
@callbacks.callback_query(F.data.startswith('admin_sends_novip_'))
async def admin_sends_no_vip(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    page = int(call.data.split('_')[3])
    try:
        if data:
            if data['message_id_1']:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=data['message_id_1'])
                await state.clear()
    except:
        pass
    await call.message.edit_text(text='Меню отправки сообщений для не VIP:',
                                 reply_markup=await kb.admin_sends_novip_keyboard(await get_sends(), page))
@callbacks.callback_query(F.data.startswith('admin_send_chats_'))
async def admin_send_no_vip(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[3])
    await call.message.delete()
    await state.update_data(message_id_1=
    (await user_send_message(bot=bot, user_id=call.message.chat.id, send_id=send_id)).message_id)
    await state.update_data(message_id_2=(await call.message.answer(text='Начать рассылку?',
                            reply_markup=await kb.admin_accept_send_novip_keyboard(send_id))).message_id)
@callbacks.callback_query(F.data.startswith('admin_accept_send_chats_'))
async def admin_accept_send_chats(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    chats = await get_chats()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_1'])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_2'])
    msg = await call.message.answer(text=f'Рассылка начата, примерное время отправки: {len(chats) * 0.05} секунд')
    for chat in chats:
        if chat[0] != call.message.chat.id:
            await user_send_message(user_id=chat[0], bot=bot, send_id=send_id)
    await bot.edit_message_text(text='Рассылка завершена', message_id=msg.message_id, chat_id=call.message.chat.id,
                                reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.clear()
@callbacks.callback_query(F.data.startswith('admin_send_novip_'))
async def admin_send_no_vip(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[3])
    await call.message.delete()
    await state.update_data(message_id_1=
    (await user_send_message(bot=bot, user_id=call.message.chat.id, send_id=send_id)).message_id)
    await state.update_data(message_id_2=(await call.message.answer(text='Начать рассылку?',
                            reply_markup=await kb.admin_accept_send_novip_keyboard(send_id))).message_id)
@callbacks.callback_query(F.data.startswith('admin_accept_send_novip_'))
async def admin_accept_send_novip(call: CallbackQuery, bot: Bot, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    users = await get_users()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_1'])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=(await state.get_data())['message_id_2'])
    msg = await call.message.answer(text=f'Рассылка начата, примерное время отправки: {len(users) * 0.05} секунд')
    for user in users:
        if not await check_vip(user[0]):
            if user[0] != call.message.chat.id:
                await user_send_message(user_id=user[0], bot=bot, send_id=send_id)
    await bot.edit_message_text(text='Рассылка завершена', message_id=msg.message_id, chat_id=call.message.chat.id,
                                reply_markup=await kb.admin_sends_novip_keyboard(await get_sends()))
    await state.clear()
@callbacks.callback_query(F.data == 'admin_chats')
async def admin_groups(call: CallbackQuery):
    await call.message.edit_text(text='Меню групп:', reply_markup=await kb.admin_chats_keyboard(await get_chats()))
@callbacks.callback_query(F.data.startswith('admin_chat_'))
async def admin_chat(call: CallbackQuery):
    chat_id = int(call.data.split('_')[2])
    chat = await get_chat(chat_id)
    await call.message.edit_text(text=f'Группа {chat[1]}', reply_markup=await kb.admin_chat_keyboard(chat_id))
@callbacks.callback_query(F.data.startswith('admin_delete_chat_'))
async def admin_delete_chat(call: CallbackQuery):
    chat_id = int(call.data.split('_')[3])
    await call.message.edit_text(text='Подтвердить удаление группы?',
                                 reply_markup=await kb.admin_accept_delete_chat_keyboard(chat_id))
@callbacks.callback_query(F.data.startswith('admin_accept_delete_chat_'))
async def admin_accept_delete_chat(call: CallbackQuery):
    chat_id = int(call.data.split('_')[4])
    await delete_chat(chat_id)
    await call.message.edit_text(text='Группа удалена',
                                 reply_markup=await kb.admin_back_to_chats_keyboard())
@callbacks.callback_query(F.data.startswith('admin_sends_chats_'))
async def admin_send_chats(call: CallbackQuery, state: FSMContext, bot: Bot):
    page = int(call.data.split('_')[3])
    sends = await get_sends()
    data = await state.get_data()
    try:
        if data:
            if data['message_id_1']:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=data['message_id_1'])
                await state.clear()
    except:
        pass
    await call.message.edit_text(text='Выберите сообшение для отправки в группы:',
                                 reply_markup=await kb.admin_sends_chats_keyboard(sends, page))
@callbacks.callback_query(F.data.startswith('admin_send_chat_'))
async def admin_send_chat(call: CallbackQuery, state: FSMContext, bot: Bot):
    send_id = int(call.data.split('_')[3])
    await call.message.delete()
    await state.update_data(message_id_1=
                            (await user_send_message(bot=bot, user_id=call.message.chat.id,
                                                     send_id=send_id)).message_id)
    await state.update_data(message_id_2=
    (await call.message.answer(text='Начать рассылку?', reply_markup=await kb.admin_accept_send_chats_keyboard(
                                                                            send_id))).message_id)
@callbacks.callback_query(F.data.startswith('admin_sends_database_'))
async def admin_send_database(call: CallbackQuery):
    page = int(call.data.split("_")[3])
    await call.message.delete()
    await call.message.answer(text='Список всех объявлений:',
                              reply_markup=await kb.admin_sends_database_keyboard(await get_sends(), page))
@callbacks.callback_query(F.data.startswith('admin_button_'))
async def admin_button(call: CallbackQuery, state: FSMContext):
    await state.clear()
    button_id = int(call.data.split('_')[2])
    button = await get_send_button(button_id)
    await call.message.delete()
    await call.message.answer(text=f'Кнопка {button[2]}\n{button[3]}', reply_markup=await kb.admin_button_keyboard(button))
@callbacks.callback_query(F.data.startswith('admin_delete_button_'))
async def admin_delete_button(call: CallbackQuery):
    button_id = int(call.data.split('_')[3])
    await call.message.edit_text(text='Подтвердить удаление кнопки?',
                                 reply_markup=await kb.admin_accept_delete_button_keyboard(button_id))
@callbacks.callback_query(F.data.startswith('admin_accept_delete_button_'))
async def admin_accept_delete_button(call: CallbackQuery):
    button_id = int(call.data.split('_')[4])
    button = await get_send_button(button_id)
    await delete_button(button_id)
    await call.message.edit_text(text='Кнопка удалена', reply_markup=await kb.admin_back_to_send_keyboard(button[1]))
@callbacks.callback_query(F.data.startswith('admin_url_button_'))
async def admin_url_button(call: CallbackQuery, state: FSMContext):
    button_id = int(call.data.split('_')[3])
    button = await get_send_button(button_id)
    await state.update_data(button_id=button_id, message_id=call.message.message_id)
    await call.message.edit_text(text='Введите ссылку для кнопки:',
                                 reply_markup=await kb.admin_back_to_button_keyboard(button[0]))
    await state.set_state(FSM.set_new_button_url)
@callbacks.callback_query(F.data.startswith('admin_text_button_'))
async def admin_text_button(call: CallbackQuery, state: FSMContext):
    button_id = int(call.data.split('_')[3])
    button = await get_send_button(button_id)
    await state.update_data(button_id=button_id, message_id=call.message.message_id)
    await call.message.edit_text(text='Введите текст для кнопки:',
                                 reply_markup=await kb.admin_back_to_button_keyboard(button[0]))
    await state.set_state(FSM.set_new_button_text)
@callbacks.callback_query(F.data.startswith('admin_add_button_'))
async def admin_add_button(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[3])
    await call.message.delete()
    await state.update_data(send_id=send_id, message_id=(await call.message.answer(text='Введите название кнопки:',
                                 reply_markup=await kb.admin_back_to_send_keyboard(send_id))).message_id)
    await state.set_state(FSM.set_button_text)
@callbacks.callback_query(F.data.startswith('admin_delete_send_'))
async def admin_delete_send(call: CallbackQuery):
    send_id = int(call.data.split('_')[3])
    await call.message.delete()
    await call.message.answer(text='Подтвердить удаление сообщения?',
                              reply_markup=await kb.admin_accept_delete_send_keyboard(send_id))
@callbacks.callback_query(F.data.startswith('admin_accept_delete_send_'))
async def admin_accept_delete_send(call: CallbackQuery):
    send_id = int(call.data.split('_')[4])
    await delete_send(send_id)
    await call.message.edit_text(text='Сообщение удалено',
                                 reply_markup=await kb.admin_sends_database_keyboard(await get_sends()))
@callbacks.callback_query(F.data.startswith('admin_text_send_'))
async def admin_text_send(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[3])
    await state.update_data(send_id=send_id, message_id=call.message.message_id)
    await call.message.delete()
    await state.update_data(message_id=(await call.message.answer(text='Введите текст сообщения:',
                              reply_markup=await kb.admin_back_to_send_keyboard(send_id))).message_id)
    await state.set_state(FSM.set_new_send_text)
@callbacks.callback_query(F.data.startswith('admin_media_send_'))
async def admin_media_send(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[3])
    await state.update_data(send_id=send_id, message_id=call.message.message_id)
    await call.message.delete()
    await call.message.answer(text='Отправьте медиа для сообщения:',
                              reply_markup=await kb.admin_back_to_send_keyboard(send_id))
    await state.set_state(FSM.set_new_send_media)
@callbacks.callback_query(F.data.startswith('admin_delete_media_send_'))
async def admin_delete_media_send(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(text='Подтвердить удаление медиа?',
                            reply_markup=await kb.admin_accept_delete_media_send_keyboard(int(call.data.split('_')[4])))
@callbacks.callback_query(F.data.startswith('admin_accept_delete_media_send_'))
async def admin_accept_delete_media_send(call: CallbackQuery):
    await delete_send_media(int(call.data.split('_')[5]))
    await call.message.edit_text(text='Медиа удалено',
                                 reply_markup=await kb.admin_back_to_send_keyboard(int(call.data.split('_')[5])))
@callbacks.callback_query(F.data == 'admin_sends')
async def admin_sends(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        if data:
            if data['message_id_1']:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=data['message_id_1'])
                await state.clear()
    except:
        pass
    await call.message.edit_text(text='Меню отправки сообщений:', reply_markup=await kb.admin_sends_keyboard())
@callbacks.callback_query(F.data == 'admin_no_text_send')
async def admin_no_text_send(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Отправьте медиа для сообщения:', reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_send_media)
@callbacks.callback_query(F.data == 'admin_add_send')
async def admin_add_send(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите текст сообщения:', reply_markup=await kb.admin_send_text_keyboard())
    await state.set_state(FSM.set_send_text)
@callbacks.callback_query(F.data == 'admin_add_send_no_text')
async def admin_add_send_no_text(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id, text=None)
    await call.message.edit_text(text='Отправьте медиа для сообщения:',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_media)
@callbacks.callback_query(F.data == 'admin_add_send_no_media')
async def admin_add_send_no_media(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id, media=None, type='text')
    data = await state.get_data()
    await add_send(text=data['text'], media=data['media'], type=data['type'])
    await call.message.edit_text(text='Сообщение добавлено', reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.clear()
@callbacks.callback_query(F.data.startswith('admin_add_media_send_'))
async def admin_add_media_send(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(message_id=(await call.message.answer(text='Отправьте медиа для сообщения:',
                         reply_markup=await kb.admin_back_keyboard())).message_id, send_id=int(call.data.split('_')[4]))
    await state.set_state(FSM.add_send_photo)
@callbacks.callback_query(F.data.startswith('admin_late_send_all_'))
async def admin_late_send_all(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='all')
    await call.message.edit_text(text='Введите время отправки сообщения (гггг-мм-дд чч:мм):',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_time)
@callbacks.callback_query(F.data.startswith('admin_late_send_vip_'))
async def admin_late_send_vip(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='vip')
    await call.message.edit_text(text='Введите время отправки сообщения (гггг-мм-дд чч:мм):',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_time)
@callbacks.callback_query(F.data.startswith('admin_late_send_novip_'))
async def admin_late_send_no_vip(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='novip')
    await call.message.edit_text(text='Введите время отправки сообщения (гггг-мм-дд чч:мм):',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_time)
@callbacks.callback_query(F.data.startswith('admin_late_send_chats_'))
async def admin_late_send_chat(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='chat')
    await call.message.edit_text(text='Введите время отправки сообщения (гггг-мм-дд чч:мм):',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_time)
@callbacks.callback_query(F.data.startswith('admin_interval_send_all_'))
async def admin_interval_send_all(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='all')
    await call.message.edit_text(text='Введите интервал отправки сообщения(м - минуты, ч - часы, д - дни, н - недели, '
                                 'стандартное значение - дни)::',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_interval)
@callbacks.callback_query(F.data.startswith('admin_interval_send_vip_'))
async def admin_interval_send_vip(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='vip')
    await call.message.edit_text(text='Введите интервал отправки сообщения(м - минуты, ч - часы, д - дни, н - недели, '
                                 'стандартное значение - дни):',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_interval)
@callbacks.callback_query(F.data.startswith('admin_interval_send_novip_'))
async def admin_interval_send_no_vip(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='novip')
    await call.message.edit_text(text='Введите интервал отправки сообщения(м - минуты, ч - часы, д - дни, н - недели, '
                                 'стандартное значение - дни):',
                                 reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_interval)
@callbacks.callback_query(F.data.startswith('admin_interval_send_chats_'))
async def admin_interval_send_chat(call: CallbackQuery, state: FSMContext):
    send_id = int(call.data.split('_')[4])
    await state.update_data(message_id=call.message.message_id, send_id=send_id, target='chat')
    await call.message.edit_text(text='Введите интервал отправки сообщения(м - минуты, ч - часы, д - дни, н - недели, '
                                 'стандартное значение - дни):', reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_send_interval)
@callbacks.callback_query(F.data == 'admin_menu')
async def menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    game = await get_last_game()
    if game is None:
        active = 2
    else:
        active = game[4]
    messages_count = await get_unread_messages_count(call.message.chat.id)
    if await is_moderator(call.message):
        await call.message.edit_text(text='Меню модератора:',
                                     reply_markup=await kb.moderator_keyboard(active=active))
        return
    await call.message.edit_text(text='Меню администратора:',
                                 reply_markup=await kb.admin_keyboard(active=active, messages_count=messages_count))
@callbacks.callback_query(F.data == 'check_subscribe')
async def check_subscribe(call: CallbackQuery, bot: Bot, state: FSMContext):
    buttons = await is_chat_member(message=call.message, bot=bot)
    if not buttons:
        await start(message=call.message, bot=bot, state=state)
@callbacks.callback_query(F.data == 'send_cash')
async def send_cash(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='📲  <b>Введите никнейм пользователя для отправки денежных средств:</b>',
                                 reply_markup=await kb.user_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_username_to_send_cash)
@callbacks.callback_query(F.data == 'admin_new_game')
async def admin_new_game(call: CallbackQuery, state: FSMContext):
    game = await get_active_game()
    if game:
        await call.message.edit_text(text='Активная игра уже существует. Во время игры нельзя создать новую игру',
                                     reply_markup=await kb.admin_back_keyboard())
        return
    await call.message.edit_text(text='Введите название игры (для сохранения её в базу данных)\n'
                                      'Это название будет отображаться в списке проведённых игр',
                                 reply_markup=await kb.admin_new_game())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_game_name)
@callbacks.callback_query(F.data == 'admin_loto_settings')
async def admin_loto_settings(call: CallbackQuery):
    await call.message.edit_text(text='Настройки лотерей:',
                                 reply_markup=await kb.admin_loto_settings_keyboard())
@callbacks.callback_query(F.data == 'admin_moment_loto_settings')
async def admin_moment_loto_settings(call: CallbackQuery):
    type_ = ''
    match LOTO_TYPE[0]:
        case 'standart':
            type_ = 'стандартная'
        case 'low':
            type_ = 'низкая'
        case 'hight':
            type_ = 'высокая'
        case 'simple':
            type_ = 'простая'
        case 'loser':
            type_ = 'проигрышная'
    await call.message.edit_text(text=f'Настройки моментальной лотереи:\nУстановлен тип: {type_}\n'
                                      f'Минимальная ставка: {LOTO_LIMIT[0]}\nМаксимальная ставка: {LOTO_LIMIT[1]}',
                                 reply_markup=await kb.admin_moment_loto_settings_keyboard())
@callbacks.callback_query(F.data == 'admin_moment_test')
async def admin_moment_loto_test(call: CallbackQuery):
    await call.message.edit_text('Тестирование моментальной лотереи начато')
    total, wins = 0, 0
    for i in range(1000):
        start_value, value = 1000, 1000
        if random.randint(0, 99) < 95:
            res = random.randint(0, 9)
        else:
            res = 0
        if LOTO_TYPE[0] == 'standart':
            match res:
                case 0:
                    value = start_value
                case 1:
                    value *= 2
                    wins += 1
                case 2:
                    value *= 3
                    wins += 1
                case 3:
                    value *= 4
                    wins += 1
                case _:
                    value = 0
        elif LOTO_TYPE[0] == 'low':
            match res:
                case 0:
                    value = 0
                case 1:
                    value *= 2
                    wins += 1
                case 2:
                    value *= 3
                    wins += 1
                case 3:
                    value *= 4
                    wins += 1
                case 4:
                    pass
                case _:
                    value = 0
        elif LOTO_TYPE[0] == 'hight':
            match res:
                case 0:
                    value *= 2
                    wins += 1
                case 1:
                    value *= 2
                    wins += 1
                case 2:
                    value *= 3
                    wins += 1
                case 3:
                    value *= 4
                    wins += 1
                case _:
                    value = 0
        elif LOTO_TYPE[0] == 'simple':
            match res:
                case 0:
                    value = 0
                case 1:
                    value *= 2
                    wins += 1
                case 2:
                    value *= 2
                    wins += 1
                case 3:
                    value *= 2
                    wins += 1
                case 4:
                    value *= 2
                    wins += 1
                case 5:
                    value *= 2
                    wins += 1
                case _:
                    value = 0
        elif LOTO_TYPE[0] == 'loser':
            match res:
                case 0:
                    pass
                case 1:
                    value *= 2
                    wins += 1
                case 2:
                    value = 0
                case 3:
                    value *= 4
                    wins += 1
                case _:
                    value = 0
        total += value
    await call.message.edit_text('Тестирование моментальной лотереи завершено\nрезультаты:\nВсего попыток 1000\n'
                                 f'Размер ставки: 1000\nОбщая сумма {1000*1000}\nПобед: {wins}\n'
                                 f'Проигрышей: {1000-wins}\nОбщий выигрыш: {total}\nДоход со ставок: '
                                 f'{1000*1000-total}',
                                 reply_markup=await kb.admin_moment_loto_settings_keyboard())

@callbacks.callback_query(F.data == 'admin_moment_change_chance')
async def admin_moment_change_chance(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Выберите тип лотереи:',
                                 reply_markup=await kb. admin_moment_loto_type_keyboard(LOTO_TYPE[0]))
    await state.set_state(FSM.set_moment_loto_chance)
@callbacks.callback_query(F.data == 'admin_moment_change_coefficient')
async def admin_moment_change_coefficient(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите коэффициент умноения выигрыша:',
                                 reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_moment_loto_coefficient)
@callbacks.callback_query(F.data == 'admin_daily_loto_settings')
async def admin_daily_loto_settings(call: CallbackQuery):
    await call.message.edit_text(text=f'<b>Настройки ежедневной лотереи:\n Текущие настройки:</b>\nСтартовая сумма: '
                                      f'<i>{DAILY_LOTO[0]}\n Коэффициент умножения: {DAILY_LOTO[1]}</i>',
                                 reply_markup=await kb.admin_daily_loto_settings_keyboard())
@callbacks.callback_query(F.data == 'admin_weekly_loto_settings')
async def admin_weekly_loto_settings(call: CallbackQuery):
    await call.message.edit_text(text=f'<b>Настройки еженедельной лотереи:\n Текущие настройки:</b>\nСтартовая сумма: '
                                      f'<i>{WEEKLY_LOTO[0]}\n Коэффициент умножения: {WEEKLY_LOTO[1]}</i>',
                                 reply_markup=await kb.admin_weekly_loto_settings_keyboard())
@callbacks.callback_query(F.data == 'admin_monthly_loto_settings')
async def admin_monthly_loto_settings(call: CallbackQuery):
    await call.message.edit_text(text=f'<b>Настройки ежемесячной лотереи:\nТекущие настройки:</b>\nСтартовая сумма: '
                                      f'<i>{MONTHLY_LOTO[0]}\nКоэффициент умножения: {MONTHLY_LOTO[1]}</i>',
                                 reply_markup=await kb.admin_monthly_loto_settings_keyboard())
@callbacks.callback_query(F.data == 'admin_daily_change_count')
async def admin_daily_change_count(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите стартовую сумму для ежедневной лотереи:',
                                 reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_daily_loto_value)
@callbacks.callback_query(F.data == 'admin_daily_change_coefficient')
async def admin_daily_change_coefficient(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите коэффициент умножения для ежедневной лотереи:',
                                 reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_daily_loto_coefficient)
@callbacks.callback_query(F.data == 'admin_weekly_change_count')
async def admin_weekly_change_count(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите стартовую сумму для еженедельной лотереи:',
                                 reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_weekly_loto_value)
@callbacks.callback_query(F.data == 'admin_weekly_change_coefficient')
async def admin_weekly_change_coefficient(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите коэффициент умножения для еженедельной лотереи:',
                                 reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_weekly_loto_coefficient)
@callbacks.callback_query(F.data == 'admin_monthly_change_count')
async def admin_monthly_change_count(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите стартовую сумму для ежемесячной лотереи:',
                                 reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_monthly_loto_value)
@callbacks.callback_query(F.data == 'admin_monthly_change_coefficient')
async def admin_monthly_change_coefficient(call: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите коэффициент умножения для ежемесячной лотереи:',
                                 reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_monthly_loto_coefficient)
@callbacks.callback_query(F.data == 'check_join_subscribe')
async def check_join_subscribe(call: CallbackQuery, bot: Bot):
    buttons = await is_chat_member(message=call.message, bot=bot)
    if not buttons:
        await user_game(call, bot)
@callbacks.callback_query(F.data == 'admin_new_game_cancel')
async def admin_new_game_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    game = await get_last_game()
    if game is None:
        active = 2
    else:
        active = game[4]
    await call.message.edit_text(text='Меню администратора:',
                                 reply_markup=await kb.admin_keyboard(active=active))
@callbacks.callback_query(F.data == 'admin_current_game')
async def admin_current_game(call: CallbackQuery):
    game = await get_last_game()
    if game:
        if game[4] == 1:
            status = 'Активна'
            text = (f'<b>Текущая игра: {game[1]}\n'
                   f'Количество игроков: {game[2]}\n'
                   f'Количество победителей: {game[3]}\n'
                   f'Статус: {status}</b>\n'
                   f'<i>Дата начала: {game[5]}</i>')
        else:
            status = 'Неактивна'
            text = (f'<b>Текущая игра: {game[1]}\n'
                   f'Количество игроков: {game[2]}\n'
                   f'Количество победителей: {game[3]}\n'
                   f'Статус: {status}</b>\n'
                   f'<i>(шаблон, можно бесследно удалить)</i>')
        await call.message.edit_text(text=text, reply_markup=await kb.current_game_keyboard(game=game))
    else:
        await call.message.edit_text(text='Текущих игр нет', reply_markup=await kb.admin_keyboard())
@callbacks.callback_query(F.data.startswith('admin_del_game_'))
async def admin_del_game(call: CallbackQuery):
    game_id = int(call.data.split('_')[3])
    await delete_game(game_id)
    await call.message.edit_text(text='Шаблон игры удалён', reply_markup=await kb.admin_keyboard())
@callbacks.callback_query(F.data.startswith('admin_start_game_'))
async def admin_start_game(call: CallbackQuery, bot: Bot):
    game_id = int(call.data.split('_')[3])
    await start_game(game_id)
    game = await get_game(game_id=game_id)
    users = await get_users()
    await call.message.edit_text(text=f'Игра начата ({(len(users) + len(CHATS_IDS))*0.09} секунд на отправку ...)')
    prizes = await get_prizes(game_id)
    prizes_count = 0
    for prize in prizes:
        prizes_count += prize[3]
    if CHATS_IDS:
        for chat in CHATS_IDS:
            try:
                pin = await bot.send_message(chat_id=chat, text=f'<b>✨  Началась новая игра "{game[1]}"!\n'
                                                                f'⚠  Количество мест: {game[2]}\n</b>'
                                                                f'<i>🎁  Количество призовых мест: {prizes_count}</i>'
                                             f'\nДля участия в игре перейдите в бота', reply_markup=await kb.bot_url())
                await bot.pin_chat_message(chat_id=chat, message_id=pin.message_id)
            except TelegramBadRequest:
                pass
            await add_pin(game_id=game_id, message_id=pin.message_id, chat_id=chat)
            await asyncio.sleep(0.09)
    for user in users:
        if True:
            await asyncio.sleep(0.09)
            if True:
                try:
                    await bot.send_message(chat_id=user[0], text=f'<b>✨  Началась новая игра "{game[1]}"!</b>\n'
                                                                 f'<i>⚠  Количество мест: {game[2]}\n🎁  <b>Количество '
                                                                 f'призовых мест: {prizes_count}</b></i>',
                                           reply_markup=await kb.user_game_keyboard(game_id=game_id))
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    await bot.send_message(chat_id=user[0], text=f'<b>✨  Началась новая игра "{game[1]}"!</b>\n'
                                                                 f'<i>⚠  Количество мест: {game[2]}\n🎁  <b>Количество '
                                                                 f'призовых мест: {prizes_count}</b></i>',
                                           reply_markup=await kb.user_game_keyboard(game_id=game_id))
                except TelegramBadRequest:
                    pass
    await call.message.edit_text(text=f'Игра "{game[1]}" начата!', reply_markup=await kb.admin_keyboard(game[4]))
@callbacks.callback_query(F.data.startswith('admin_end_game'))
async def admin_end_game(call: CallbackQuery):
    game_id = int(call.data.split('_')[3])
    game = await get_game(game_id=game_id)
    await call.message.edit_text(text=f'Вы действительно хотите завершить игру "{game[1]}?',
                                 reply_markup=await kb.admin_end_game(game_id))
@callbacks.callback_query(F.data.startswith('admin_ending_game'))
async def admin_ending_game(call: CallbackQuery, bot: Bot):
    game_id = int(call.data.split('_')[3])
    pins = await get_pins(game_id=game_id)
    if pins:
        for pin in pins:
            await bot.unpin_chat_message(chat_id=pin[2], message_id=pin[1])
            await asyncio.sleep(0.05)
    game = await get_game(game_id=game_id)
    prizes = await get_prizes(game_id)
    prizes_count = 0
    for prize in prizes:
        prizes_count += prize[3]
    prizes = await get_prizes(game_id)
    users = await get_game_users(game_id=game_id)
    await call.message.edit_text(text=f'Игра "{game[1]}" завершается, отправка результатов '
                                      f'({(prizes_count+len(users)+len(CHATS_IDS))*0.09} cекунд)',
                                 reply_markup=await kb.admin_keyboard())
    if users:
        for user in users:
            if user[0] not in ADMINS_IDS:
                await asyncio.sleep(0.09)
                await bot.send_message(chat_id=user[0], text=f'🎉  <b>Игра "{game[1]}" завершена!</b>\n<i>🎁  Результаты '
                                                             f'будут отправлены в течении некоторого времени</i>')
    if CHATS_IDS:
        for chat in CHATS_IDS:
            await asyncio.sleep(0.09)
            await bot.send_message(chat_id=chat, text=f'🎉  <b>Игра "{game[1]}" завершена!</b>\n<i>🎁  Результаты '
                                                      f'будут отправлены в течении некоторого времени</i>')
    counter = 0
    text = ''
    chat_text = f'<b>✨  Игра "{game[1]}" завершена!\nСписок победителей:</b>\n'
    users = await get_game_users(game_id=game_id)
    await end_game(game_id=game_id)
    for prize in prizes:
        count = prize[3]
        while count >= 1:
            if users:
                winner = random.choice(users)
                winner_user = await get_user(user_id=winner[0])
                await set_game_timeout(user_id=winner[0])
                if winner_user[12] == 1:
                    chat_text += f'<i>🕶 Анонимный пользователь: {prize[1]}\n</i>'
                else:
                    chat_text += f'<i>@{winner_user[1]}: {prize[1]}\n</i>'
                users.remove(winner)
                user = await get_user(user_id=winner[0])
                await asyncio.sleep(0.09)
                try:
                    match_ = re.match(r"(\d+)", prize[1].lower())
                    try:
                        if match_:
                            value = int(match_.group(1))
                            await update_balance(winner[0], value)
                    except ValueError:
                        await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Вы победили в игре!</b>\n<i>🎁  '
                                               f'Ваш приз: <b>{prize[1]}</b></i>\n<i>✨  Для получения приза необходимо'
                                               f' написать администратору!</i>',
                                               reply_markup=await kb.admin_url_keyboard())
                    await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Вы победили в игре!</b>\n<i>🎁  Ваш приз: '
                                           f'<b>{prize[1]}</b></i>\n<i>✨  Приз начислен на ваш баланс!</i>',
                                           reply_markup=await kb.user_back_keyboard())
                    counter += 1
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    try:
                        await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Вы победили в игре!</b>\n<i>🎁  '
                                               f'Ваш приз: <b>{prize[1]}</b></i>\n<i>✨  Для получения приза необходимо'
                                               f' написать администратору!</i>',
                                               reply_markup=await kb.admin_url_keyboard())
                    except Exception as e:
                        print(e)
                        text += f'@{user[1]}: {prize[1]}\n'
                await add_winner(winner[0], prize[0], game_id)
                count -= 1
            else:
                await call.message.edit_text(text=f'В игре не было участников, игра "{game[1]}" завершена!',
                                             reply_markup=await kb.admin_keyboard())
                break
        await asyncio.sleep(0.09)
    await end_game(game_id=game_id)
    await call.message.edit_text(
        text=f'Игра "{game[1]}" завершена!\nНеудачных отправок: {prizes_count - counter}\n{text}',
        reply_markup=await kb.admin_keyboard())
    try:
        if pins:
            for pin in pins:
                await bot.unpin_chat_message(chat_id=pin[2], message_id=pin[1])
                await asyncio.sleep(0.09)
    except Exception as e:
        print(e)
    chat_text += f'\n<i><b>🎁  Поздравляем победителей!</b></i>'
    if CHATS_IDS:
        for chat in CHATS_IDS:
            await asyncio.sleep(0.09)
            pin = await bot.send_message(chat_id=chat, text=chat_text, reply_markup=await kb.bot_url())
            await bot.pin_chat_message(chat_id=chat, message_id=pin.message_id)

@callbacks.callback_query(F.data.startswith('admin_canc_game'))
async def admin_end_game(call: CallbackQuery):
    game_id = int(call.data.split('_')[3])
    game = await get_game(game_id=game_id)
    await call.message.edit_text(text=f'Вы действительно хотите отменить игру "{game[1]}?',
                                 reply_markup=await kb.admin_canc_game_keyboard(game_id))
@callbacks.callback_query(F.data.startswith('admin_cancel_game'))
async def admin_cancel_game(call: CallbackQuery):
    game_id = int(call.data.split('_')[3])
    game = await get_game(game_id)
    await delete_game(game_id)
    await call.message.edit_text(text=f'Игра "{game[1]}" отменена!', reply_markup=await kb.admin_send_end_game(game_id))
@callbacks.callback_query(F.data.startswith('admin_send_end'))
async def admin_send_end(call: CallbackQuery, bot: Bot):
    game_id = int(call.data.split('_')[3])
    users = await get_game_users(game_id=game_id)
    await call.message.edit_text(text=f'Отправка сообщения об отмене игры...({(len(users)+len(CHATS_IDS))*0.05} '
                                      f'cекунд)', reply_markup=None)
    for user in users:
        await asyncio.sleep(0.05)
        try:
            await bot.send_message(chat_id=user[0], text=END_GAME_MESSAGE, reply_markup=await kb.user_back_keyboard())
        except TelegramBadRequest:
            pass
    for chat in CHATS_IDS:
        await asyncio.sleep(0.05)
        try:
            await bot.send_message(chat_id=chat, text=END_GAME_MESSAGE, reply_markup=await kb.bot_url())
        except TelegramBadRequest:
            pass
    await call.message.edit_text(text='Сообщение об отмене игры отправлено', reply_markup=await kb.admin_keyboard())
@callbacks.callback_query(F.data.startswith('admin_add_prize'))
async def admin_add_prize(call: CallbackQuery, state: FSMContext):
    game_id = int(call.data.split('_')[3])
    await state.update_data(game_id=game_id)
    await call.message.edit_text(text='Введите текст приза:', reply_markup=await kb.admin_game_prize_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_prize_text)
@callbacks.callback_query(F.data.startswith('admin_game_prizes_'))
async def admin_game_prizes(call: CallbackQuery):
    game_id = int(call.data.split('_')[3])
    game = await get_game(game_id)
    prizes = await get_prizes(game_id)
    prizes_count = 0
    for prize in prizes:
        prizes_count += prize[3]
    if prizes:
        await call.message.edit_text(text=f'Призовых мест в игре: {game[3]}\n'
                                     f'Количество добавленных призов: {prizes_count}\n'
                                     'Призы текущей игры:',
                                     reply_markup=await kb.admin_prizes_keyboard(prizes=prizes, game_id=game_id))
    else:
        await call.message.edit_text(text='В данный момент в игре не добавлены призы\n'
                                          f'Призовых мест запланировано в игре: {game[3]}',
                                     reply_markup=await kb.admin_prizes_keyboard(prizes=prizes, game_id=game_id))
@callbacks.callback_query(F.data.startswith('admin_current_prize'))
async def admin_current_prize(call: CallbackQuery, state: FSMContext):
    await state.clear()
    prize_id = int(call.data.split('_')[3])
    prize = await get_prize(prize_id)
    await call.message.edit_text(text=f'Выбранный приз: {prize[1]} в количестве {prize[3]} шт',
                                 reply_markup=await kb.admin_current_prize_keyboard(prize_id=prize_id))
@callbacks.callback_query(F.data.startswith('admin_del_prize'))
async def admin_del_prize(call: CallbackQuery):
    prize_id = int(call.data.split("_")[3])
    prize = await get_prize(prize_id=prize_id)
    await del_prize(prize_id)
    prizes = await get_prizes(prize[2])
    await call.message.edit_text(text=f'Приз {prize[1]} - {prize[3]} шт был удалён',
                                 reply_markup=await kb.admin_prizes_keyboard(prizes, prize[2]))
@callbacks.callback_query(F.data.startswith('admin_text_prize'))
async def admin_text_prize(call: CallbackQuery, state: FSMContext):
    prize_id = int(call.data.split('_')[3])
    await state.update_data(prize_id=prize_id)
    await call.message.edit_text(text='Напиши новый текст приза:',
                                 reply_markup=await kb.admin_text_prize_keyboard(prize_id=prize_id))
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_new_prize_text)
@callbacks.callback_query(F.data.startswith('admin_count_prize'))
async def admin_text_prize(call: CallbackQuery, state: FSMContext):
    prize_id = int(call.data.split('_')[3])
    await state.update_data(prize_id=prize_id)
    await call.message.edit_text(text='Напиши новое количестао призов:',
                                 reply_markup=await kb.admin_text_prize_keyboard(prize_id=prize_id))
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_new_prize_count)
@callbacks.callback_query(F.data.startswith('admin_users_game'))
async def admin_users_game(call: CallbackQuery):
    game_id = int(call.data.split('_')[3])
    game = await get_game(game_id)
    users = await get_game_users(game_id=game_id)
    text = f'Участники игры "{game[1]}":\nКоличество участников: {len(users)}\n'
    for user in users:
        user_info = await get_user(user_id=user[0])
        if user_info[0]:
            text += f'@{user_info[1]}\n'
        else:
            text += f'@{user_info[0]} - {user_info[2]}\n'
    await call.message.edit_text(text=text, reply_markup=await kb.admin_back_keyboard())
@callbacks.callback_query(F.data == 'admin_game_history')
async def admin_game_history(call: CallbackQuery):
    games = await get_games_history()
    text = 'История игр:\n'
    if games:
        await call.message.edit_text(text=text, reply_markup=await kb.admin_history_keyboard(games=games))
    else:
        await call.message.edit_text(text='История игр пуста', reply_markup=await kb.admin_back_keyboard())
@callbacks.callback_query(F.data.startswith('admin_shablon_prize_'))
async def admin_shablon_prize(call: CallbackQuery):
    game_id = int(call.data.split('_')[3])
    prizes = await get_all_prizes()
    if prizes:
        for prize in prizes:
            counter = 0
            for i in prizes:
                if prize[1] == i[1]:
                    if counter != 0:
                        prizes.remove(i)
                    if counter == 0:
                        counter += 1
    prizes = prizes[::-1]
    await call.message.edit_text(text='Шаблон призов:\n<i>Для добавления нажмите на шаблон</i>',
                                 reply_markup=await kb.admin_shablon_prizes_keyboard(prizes=prizes, game_id=game_id))
@callbacks.callback_query(F.data.startswith('admin_shablon_add'))
async def admin_shablon_add(call: CallbackQuery, state: FSMContext):
    prize_id = int(call.data.split('_')[3])
    game_id = int(call.data.split('_')[4])
    await state.update_data(prize_id=prize_id)
    await state.update_data(game_id=game_id)
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(text='Введите количество призов:', reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_shablon_count)

@callbacks.callback_query(F.data.startswith('admin_history_'))
async def admin_history(call: CallbackQuery):
    game_id = int(call.data.split('_')[2])
    game = await get_game(game_id=game_id)
    winners = await get_game_winners(game_id=game_id)
    text = 'Информация об игре:\n'
    text += f'Название игры: {game[1]}\n'
    text += f'Количество мест: {game[2]}\n'
    text += f'Количество победителей: {game[3]}\n'
    text += f'Дата начала: {game[5]}\n'
    text += f'Дата окончания: {game[6]}\n'
    text += f'Призовые места:\n'
    for winner in winners:
        user = await get_user(user_id=winner[0])
        prize = await get_prize(prize_id=winner[1])
        if user[1]:
            text += f'@{user[1]} - {prize[1]}\n'
        else:
            text += f'@{user[2]} - {prize[1]}\n'
    await call.message.edit_text(text=text, reply_markup=await kb.admin_back_keyboard())
@callbacks.callback_query(F.data.startswith('user_game'))
async def user_game(call: CallbackQuery, bot: Bot):
    game_id = int(call.data.split('_')[2])
    buttons = await is_chat_member(message=call.message, bot=bot)
    if not buttons:
        if await is_banned(user_id=call.from_user.id):
            await call.message.edit_text(text='⛔  Вы заблокированы!', reply_markup=None)
            return
        user = await get_user(user_id=call.message.chat.id)
        if user[10]:
            is_vip = datetime.datetime.fromisoformat(user[10]) > datetime.datetime.now()
        else:
            is_vip = False
        timeout = await get_game_timeout(user_id=call.message.chat.id)
        if not is_vip:
            if timeout:
                await call.message.edit_text(text='⚠  <b>Вы уже учавствовали в игре недавно</b>',
                                             reply_markup=await kb.user_back_keyboard())
                return
        if await join_game(user_id=call.from_user.id, game_id=game_id):
            await call.message.edit_text(text='<b>✅  Вы участвуете в игре!</b>',
                                         reply_markup=await kb.user_back_keyboard())
            game = await get_active_game()
            game_prizes = await get_prizes(game_id=game_id)
            count = 0
            for prize in game_prizes:
                count += prize[3]
            if await number_of_users(game[0]) >= game[2]:
                game = await get_game(game_id=game_id)
                prizes = await get_prizes(game_id)
                prizes_count = 0
                await end_game(game_id=game_id)
                for prize in prizes:
                    prizes_count += prize[3]
                users = await get_game_users(game_id=game_id)
                await bot.send_message(chat_id=ADMINS_IDS[0],
                                       text=f'Игра "{game[1]}" завершается, отправка результатов '
                                            f'({(prizes_count+len(users)+len(CHATS_IDS))* 0.06} '
                                            f'cекунд)', reply_markup=await kb.admin_keyboard())
                for user in users:
                    if user[0] not in ADMINS_IDS:
                        await asyncio.sleep(0.06)
                        await bot.send_message(chat_id=user[0],
                                               text=f'🎉  <b>Игра "{game[1]}" завершена!</b>\n<i>🎁  Результаты '
                                                    f'будут отправлены в течении некоторого времени</i>',
                                               reply_markup=await kb.user_back_keyboard())
                if CHATS_IDS:
                    for chat in CHATS_IDS:
                        await asyncio.sleep(0.06)
                        await bot.send_message(chat_id=chat,
                                               text=f'🎉  <b>Игра "{game[1]}" завершена!</b>\n<i>🎁  Результаты '
                                                    f'будут отправлены в течении некоторого времени</i>')
                counter = 0
                pins = await get_pins(game_id=game_id)
                if pins:
                    for pin in pins:
                        await bot.unpin_chat_message(chat_id=pin[2], message_id=pin[1])
                        await asyncio.sleep(0.05)
                game = await get_game(game_id=game_id)
                text = ''
                chat_text = f'<b>✨  Игра "{game[1]}" завершена!\nСписок победителей:</b>\n'
                users = await get_game_users(game_id=game_id)
                for prize in prizes:
                    count = prize[3]
                    while count >= 1:
                        winner = random.choice(users)
                        users.remove(winner)
                        user = await get_user(user_id=winner[0])
                        await set_game_timeout(user_id=user[0])
                        if user[12] == 1:
                            chat_text += f'<i>🕶 Анонимный пользователь: {prize[1]}\n</i>'
                        else:
                            chat_text += f'<i>@{user[1]}: {prize[1]}\n</i>'
                        try:
                            match_ = re.match(r"(\d+)", prize[1].lower())
                            try:
                                value = int(match_.group(1))
                                await update_balance(winner[0], value)
                            except ValueError:
                                await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Вы победили в игре!</b>\n<i>🎁  '
                                                                               f'Ваш приз: <b>{prize[1]}</b></i>\n'
                                                                               f'<i>✨  Для получения приза необзодимо'
                                                                               f' написать администратору!</i>',
                                                       reply_markup=await kb.admin_url_keyboard())
                            await bot.send_message(chat_id=winner[0],
                                                   text=f'🎉  <b>Вы победили в игре!</b>\n<i>🎁  Ваш приз: <b>'
                                                        f'{prize[1]}</b></i>\n<i>✨  Приз начислен на ваш баланс!</i>',
                                                   reply_markup=await kb.user_back_keyboard())
                            counter += 1
                        except Exception:
                            await asyncio.sleep(0.06)
                            try:
                                await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Вы победили в игре!</b>\n<i>🎁  '
                                                                               f'Ваш приз: <b>{prize[1]}</b></i>\n'
                                                                               f'<i>✨  Для получения приза необзодимо'
                                                                               f' написать администратору!</i>',
                                                       reply_markup=await kb.admin_url_keyboard())
                                counter += 1
                            except Exception as e:
                                print(e)
                                text += f'@{user[1]}: {prize[1]}\n'
                        await add_winner(winner[0], prize[0], game_id)
                        count -= 1
                await bot.send_message(chat_id=ADMINS_IDS[0], text=f'Игра "{game[1]}" завершена!\nНеудачных отправок: '
                                       f'{prizes_count - counter}\n{text}', reply_markup=await kb.admin_keyboard())
                chat_text += f'\n<i><b>🎁  Поздравляем победителей!</b></i>'
                if CHATS_IDS:
                    for chat in CHATS_IDS:
                        await asyncio.sleep(0.06)
                        pin = await bot.send_message(chat_id=chat, text=chat_text, reply_markup=await kb.bot_url())
                        await bot.pin_chat_message(chat_id=chat, message_id=pin.message_id)
            else:
                pins = await get_pins(game_id=game_id)
                prizes = await get_prizes(game_id)
                prizes_count = 0
                for prize in prizes:
                    prizes_count += prize[3]
                if pins:
                    for pin in pins:
                        try:
                            await bot.edit_message_text(chat_id=pin[2], message_id=pin[1],
                                                        text=f'<b>✨  Началась новая игра!\n⚠  Количество мест: '
                                                        f'{game[2]}\n</b>'
                                                        f'<i>🎁  Количество призовых мест: {prizes_count}</i>'
                                                        f'\n<i>🎫  Для участия в игре перейдите в бота</i>'
                                                        f'\n<b>📃  Участники: {await number_of_users(game[0])}</b>',
                                                        reply_markup=await kb.bot_url())
                        except Exception:
                            print('chat_id: '+str(pin[2])+' message_id: '+str(pin[1])+' cant edit message')
        else:
            await call.message.edit_text(text='<b>Mеста в игре закончились!</b>',
                                         reply_markup=None)
    else:
        await call.message.edit_text(text='Для участия необxодима подписка на:',
                                     reply_markup=await kb.start_keyboard(buttons=buttons))
@callbacks.callback_query(F.data == 'moment_loto')
async def moment_loto(call: CallbackQuery):
    user = await get_user(user_id=call.message.chat.id)
    daily_user_loto = await get_daily_moment_loto_by_user_id(user_id=call.message.chat.id)
    weekly_user_loto = await get_weekly_moment_loto_by_user_id(user_id=call.message.chat.id)
    monthly_user_loto = await get_monthly_moment_loto_by_user_id(user_id=call.message.chat.id)
    if user[9] >= 1:
        text = (f'<b>💵  Ваш баланс: {user[9]}</b>\n<i>✨  Сыграно лотерей сегодня: {daily_user_loto[0]}</i>\n'
                f'<i>✨  Сыграно лотерей на этой неделе: {weekly_user_loto[0]}</i>\n'
                f'<i>✨  Сыграно лотерей в этом месяце: {monthly_user_loto[0]}</i>\n')
        await call.message.edit_text(text=text, reply_markup=await kb.moment_loto_keyboard())
    else:
        await call.message.edit_text(text='⛔  Недостаточно средств',
                                     reply_markup=await kb.user_back_keyboard())
@callbacks.callback_query(F.data.startswith('moment_loto_'))
async def moment_loto_start(call: CallbackQuery, state: FSMContext):
    user = await get_user(user_id=call.message.chat.id)
    ttype = call.data.split('_')[2]
    text = (f'<b>💵  Ваш баланс: {user[9]}</b>\n<b>Ограничения по ставкам: от {LOTO_LIMIT[0]} до {LOTO_LIMIT[1]}\n</b>'
            f'<i>✏  Введите сумму ставки:</i>')
    await call.message.edit_text(text=text, reply_markup=await kb.user_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_moment_loto_value)
    match ttype:
        case 'hell':
            await state.update_data(ttype=1)
        case 'hard':
            await state.update_data(ttype=2)
        case 'medium':
            await state.update_data(ttype=3)
        case 'easy':
            await state.update_data(ttype=4)

@callbacks.callback_query(F.data == 'm_loto_confirm')
async def m_loto_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    value = data['value']
    await update_balance(user_id=call.message.chat.id, value=(-value))
    settings = MOMENT_LOTO
    check = False
    if random.randint(0, 99) < 95:
        res = random.randint(0, 9)
    else:
        res = 0
    start_value = value
    if LOTO_TYPE[0] == 'standart':
        match res:
            case 0:
                pass
            case 1:
                value *= 2
                check = True
            case 2:
                value *= 3
                check = True
            case 3:
                value *= 4
                check = True
            case _:
                value = 0
    elif LOTO_TYPE[0] == 'low':
        match res:
            case 0:
                value = 0
            case 1:
                value *= 2
                check = True
            case 2:
                value *= 3
                check = True
            case 3:
                value *= 4
                check = True
            case 4:
                pass
            case _:
                value = 0
    elif LOTO_TYPE[0] == 'hight':
        match res:
            case 0:
                value *= 2
                check = True
            case 1:
                value *= 2
                check = True
            case 2:
                value *= 3
                check = True
            case 3:
                value *= 4
                check = True
            case _:
                value = 0
    elif LOTO_TYPE[0] == 'simple':
        match res:
            case 0:
                value = 0
            case 1:
                value *= 2
                check = True
            case 2:
                value *= 2
                check = True
            case 3:
                value *= 2
                check = True
            case 4:
                value *= 2
                check = True
            case 5:
                value *= 2
                check = True
            case _:
                value = 0
    elif LOTO_TYPE[0] == 'loser':
        match res:
            case 0:
                pass
            case 1:
                value *= 2
                check = True
            case 2:
                value = 0
            case 3:
                value *= 4
                check = True
            case _:
                value = 0
    await state.clear()
    await add_spin(user_id=call.message.chat.id)
    daily_user_loto = await get_daily_moment_loto_by_user_id(user_id=call.message.chat.id)
    weekly_user_loto = await get_weekly_moment_loto_by_user_id(user_id=call.message.chat.id)
    monthly_user_loto = await get_monthly_moment_loto_by_user_id(user_id=call.message.chat.id)
    if check:
        await add_moment_loto(user_id=call.message.chat.id, value=value, result=1, start_value=start_value)
        await update_balance(user_id=call.message.chat.id, value=value)
    else:
        await add_moment_loto(user_id=call.message.chat.id, value=value, result=0, start_value=start_value)
    if check:
        user = await get_user(user_id=call.message.chat.id)
        text = (f'🎉  <b>Вы выиграли {value}!</b>\n<b>💵  Ваш баланс: {user[9]}</b>\n<i>✨  Сыграно лотерей сегодня: '
                f'{daily_user_loto[0]}</i>\n'
                f'<i>✨  Сыграно лотерей на этой неделе: {weekly_user_loto[0]}</i>\n'
                f'<i>✨  Сыграно лотерей в этом месяце: {monthly_user_loto[0]}</i>\n')
    else:
        user = await get_user(user_id=call.message.chat.id)
        text = (f'<b>✨  В этот раз вам не повезло, но всегда можно попробовать снова!</b>\n'
                f'<b>💵  Ваш баланс: {user[9]}</b>\n<i>✨  Сыграно лотерей сегодня: '
                f'{daily_user_loto[0]}</i>\n'
                f'<i>✨  Сыграно лотерей на этой неделе: {weekly_user_loto[0]}</i>\n'
                f'<i>✨  Сыграно лотерей в этом месяце: {monthly_user_loto[0]}</i>\n')
    user = await get_user(user_id=call.message.chat.id)
    if user[9] >= 1:
        markup = await kb.moment_loto_keyboard()
    else:
        markup = await kb.user_back_keyboard()
    await call.message.edit_text(text=text, reply_markup=markup)
    await state.clear()
@callbacks.callback_query(F.data.startswith('admin_moment_loto_type_'))
async def admin_moment_loto_type(call: CallbackQuery):
    LOTO_TYPE.pop()
    LOTO_TYPE.append(call.data.split('_')[4])
    type_ = ''
    match LOTO_TYPE[0]:
        case 'standart':
            type_ = 'стандартная'
        case 'low':
            type_ = 'низкая'
        case 'hight':
            type_ = 'высокая'
        case 'simple':
            type_ = 'простая'
        case 'loser':
            type_ = 'проигрышная'
    await call.message.edit_text(text=f'Тип лотереи изменён на {type_}',
                                 reply_markup=await kb.admin_back_to_loto_settings_keyboard())



@callbacks.callback_query(F.data == 'loto_tickets')
async def loto_tickets(call: CallbackQuery):
    user = await get_user(user_id=call.message.chat.id)
    daily_loto = await get_daily_moment_loto()
    weekly_loto = await get_weekly_moment_loto()
    monthly_loto = await get_monthly_moment_loto()
    daily_prize = DAILY_LOTO[0] + DAILY_LOTO[1] * daily_loto[0]
    weekly_prize = WEEKLY_LOTO[0] + WEEKLY_LOTO[1] * weekly_loto[0]
    monthly_prize = MONTHLY_LOTO[0] + MONTHLY_LOTO[1] * monthly_loto[0]
    text = (f'<b>💵  Ваш баланс: {user[9]}\n</b><i>✏  Выберите вариант лотереи:</i>\n<b>Условия: </b>\n<i>🎟  '
            f'Ежедневный билет: 500 и 10 участий '
            f'в моментальной лотерее\n</i><i>🎟  Еженедельный билет: 1000 и 50 участий в моментальной лотерее\n</i>'
            f'<i>🎟  Ежемесячный билет: 4000 и 100 участий в моментальной лотерее</i>\n'
            f'<b>✨  Cиграно лотерей сегодня: {daily_loto[0]}</b>\n<b>💵  При победе приз: {daily_prize}!</b>\n'
            f'<b>✨  Cиграно лотерей на этой неделе: {weekly_loto[0]}</b>\n<b>💵  При победе приз: {weekly_prize}!</b>\n'
            f'<b>✨  Cиграно лотерей в этом месяце: {monthly_loto[0]}</b>\n<b>💵  При победе приз: {monthly_prize}!</b>\n'
            '<i>📅  График лотерей:\n🎫  Ежедневная: каждый день в 00:00\n🎫  Еженедельная: каждый понедельник в 00:00\n'
            '🎫  Ежемесячная: первое число каждого месяца в 00:00</i>\n')
    await call.message.edit_text(text=text, reply_markup=await kb.loto_tickets_keyboard(user))
@callbacks.callback_query(F.data == 'user_anonim')
async def user_anonim(call: CallbackQuery):
    await call.message.edit_text(text='Установлен статус анонима, имя пользователя будет скрыто в результатах игры',
                                 reply_markup=await kb.user_back_keyboard())
    await set_user_anonim(user_id=call.message.chat.id, value=1)
@callbacks.callback_query(F.data == 'user_visible')
async def user_visible(call: CallbackQuery):
    await call.message.edit_text(text='Статус анонима снят, имя пользователя будет видно в результатах игры',
                                 reply_markup=await kb.user_back_keyboard())
    await set_user_anonim(user_id=call.message.chat.id, value=0)


@callbacks.callback_query(F.data.startswith('t_ticket_'))
async def t_ticket(call: CallbackQuery):
    _type = call.data.split('_')[2]
    match _type:
        case 'daily':
            await update_balance(user_id=call.message.chat.id, value=-500)
            await get_daily_ticket(user_id=call.message.chat.id)
            await call.message.edit_text(text='✅  Вы стали участником ежедневной лотереи',
                                         reply_markup=await kb.user_back_keyboard())
        case 'weekly':
            await update_balance(user_id=call.message.chat.id, value=-1000)
            await get_weekly_ticket(user_id=call.message.chat.id)
            await call.message.edit_text(text='✅  Вы стали участником еженедельной лотереи',
                                         reply_markup=await kb.user_back_keyboard())
        case 'monthly':
            await update_balance(user_id=call.message.chat.id, value=-4000)
            await get_monthly_ticket(user_id=call.message.chat.id)
            await call.message.edit_text(text='✅  Вы стали участником ежемесячной лотереи',
                                         reply_markup=await kb.user_back_keyboard())
@callbacks.callback_query(F.data == 'admin_loto')
async def admin_loto(call: CallbackQuery):
    daily_count = await get_daily_users_count()
    weekly_count = await get_weekly_users_count()
    monthly_count = await get_monthly_users_count()
    daily_moment_loto = await get_daily_moment_loto_db()
    weekly_moment_loto = await get_weekly_moment_loto_db()
    monthly_moment_loto = await get_monthly_moment_loto_db()
    all_loto = await get_all_moment_loto()
    all_loto_payed = 0
    all_loto_winned = 0
    all_loto_count_winned = 0
    for loto in all_loto:
        all_loto_payed += loto[2]
        if loto[3] == 1:
            all_loto_winned += loto[5]
            all_loto_count_winned += 1
    daily_payed = 0
    daily_winned = 0
    daily_count_winned = 0
    weekly_payed = 0
    weekly_winned = 0
    weekly_count_winned = 0
    monthly_payed = 0
    monthly_winned = 0
    monthly_count_winned = 0
    for daily in daily_moment_loto:
        daily_payed += daily[2]
        if daily[3] == 1:
            daily_winned += daily[5]
            daily_count_winned += 1
    for weekly in weekly_moment_loto:
        weekly_payed += weekly[2]
        if weekly[3] == 1:
            weekly_winned += weekly[5]
            weekly_count_winned += 1
    for monthly in monthly_moment_loto:
        monthly_payed += monthly[2]
        if monthly[3] == 1:
            monthly_winned += monthly[5]
            monthly_count_winned += 1
    text = f'📋  <b>Статистика лотерей:</b>\n'
    if daily_count:
        text += f'📅  <b>Ежедневная лотерея:</b>\n🎟  <i>Количество участников: {daily_count[0]}</i>\n'
    if weekly_count:
        text += f'📅  <b>Еженедельная лотерея:</b>\n🎟  <i>Количество участников: {weekly_count[0]}</i>\n'
    if monthly_count:
        text += f'📅  <b>Ежемесячная лотерея:</b>\n🎟  <i>Количество участников: {monthly_count[0]}</i>\n'
    text += '\n'
    if all_loto:
        text += (f'✨  <b>Моментальные лотереи всего:\n<i>Cиграно: {len(all_loto)}\nВыиграно: {all_loto_count_winned}\n'
                 f'Сумма ставок: {all_loto_payed}\nСумма выплат победителям: {all_loto_winned}</i></b>\n')
    if daily_moment_loto:
        text += (f'✨  <b>Моментальные лотереи сегодня:\n<i>Cиграно: {len(daily_moment_loto)}\nВыиграно: '
        f'{daily_count_winned}\nСумма ставок: {daily_payed}\nСумма выплат победителям: {daily_winned}</i></b>\n')
    if weekly_moment_loto:
        text += (f'✨  <b>Моментальные лотереи на этой неделе:\n<i>Cиграно: {len(weekly_moment_loto)}\nВыиграно: '
        f'{weekly_count_winned}\nСумма ставок: {weekly_payed}\nСумма выплат победителям: {weekly_winned}</i></b>\n')
    if monthly_moment_loto:
        text += (f'✨  <b>Моментальные лотереи в этом месяце:\n<i>Cиграно: {len(monthly_moment_loto)}\nВыиграно: '
        f'{monthly_count_winned}\nСумма ставок: {monthly_payed}\nСумма выплат победителям: {monthly_winned}</i></b>\n')
    await call.message.edit_text(text=text, reply_markup=await kb.admin_back_keyboard())

@callbacks.callback_query(F.data.startswith('referrer'))
async def referrer(call: CallbackQuery):
    addresses_count = await get_active_addresses_count()
    user_address = await get_user_address(user_id=call.from_user.id)
    referrers_count = await get_referrers_count(user_id=call.from_user.id)
    if user_address:
        text = (f'🎁<b>  Вы уже получили промокод на бесплатный промокод: {user_address[0][0]}\n'
                f'✨  Поздравляем с выполнением задания!</b>')
        await call.message.edit_text(text=text, reply_markup=await kb.admin_url_keyboard())
        return
    if referrers_count >= REFERRER_MISSION:
        address = await get_free_address(call.message.chat.id)
        text = (f'<b>🎉  Поздравляем с выполнением цели!\n'
                f'<i>🎁  Вы получили промокод: {address[0]}\n</i>'
                f'📲  Отправьте его администратору чтобы выбрать бесплатный адрес</b>')
        await call.message.edit_text(text=text, reply_markup=await kb.admin_url_keyboard())
        return
    if addresses_count == 0:
        await call.message.edit_text(text='🔍 <b> Бесплатные адреса закончились</b>',
                                     reply_markup=await kb.user_back_keyboard())
        return

    else:
        text = (f'✨  <b>Особое предложение!</b>\n📬  <u>Пригласи 15 друзей и получи бесплатный адрес!\n'
                f'📃  Друзей приглашено: {referrers_count}\n⚠  Необходимо пригласить: {REFERRER_MISSION}</u>\n'
                f'✨  <b>Доступных адресов осталось: {addresses_count[0]}</b>\n'
                f'📲  <u>Ваша уникальная ссылка для приглашения друзей:</u>\n'
                f'https://t.me/{BOT_USERNAME}?start={call.message.chat.id}')
        await call.message.edit_text(text=text, reply_markup=await kb.user_back_keyboard())
@callbacks.callback_query(F.data == 'admin_addresses')
async def admin_addresses(call: CallbackQuery):
    addresses = await get_addresses()
    await call.message.edit_text(text='Все промокоды:',
                                 reply_markup=await kb.admin_addresses_keyboard(addresses=addresses))
@callbacks.callback_query(F.data.startswith('admin_address_select'))
async def admin_address_select(call: CallbackQuery):
    address_id = int(call.data.split('_')[3])
    address = await get_address(address_id=address_id)
    await call.message.edit_text(text=f'Выбранный промокод: <i>{address[1]}</i>',
                                 reply_markup=await kb.admin_address_select_keyboard(address_id))
@callbacks.callback_query(F.data.startswith('admin_address_deactivate'))
async def admin_address_deactivate(call: CallbackQuery):
    address_id = int(call.data.split('_')[3])
    await deactivate_address(address_id)
    await call.message.edit_text(text='Промокод деактивирован',
                                 reply_markup=await kb.admin_address_select_keyboard(address_id))
@callbacks.callback_query(F.data.startswith('admin_address_activate'))
async def admin_address_activate(call: CallbackQuery):
    address_id = int(call.data.split('_')[3])
    await activate_address(address_id)
    await call.message.edit_text(text='Промокод активирован',
                                 reply_markup=await kb.admin_address_select_keyboard(address_id))
@callbacks.callback_query(F.data.startswith('admin_address_delete'))
async def admin_address_delete(call: CallbackQuery):
    address_id = int(call.data.split('_')[3])
    await delete_address(address_id)
    await call.message.edit_text(text='Промокод удалён', reply_markup=await kb.admin_keyboard())
@callbacks.callback_query(F.data == 'admin_add_address')
async def admin_add_address(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Введите промокод:', reply_markup=None)
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_address)
@callbacks.callback_query(F.data == 'user_menu')
async def user_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    subscribe = await check_subscribe_db(user_id=call.message.chat.id)
    await update_username_name(user_id=call.message.chat.id, username=call.message.chat.username,
                               first_name=call.message.chat.first_name)
    if subscribe[0]:
        user = await get_user(user_id=call.message.chat.id)
        if user[10] != '':
            check = datetime.datetime.isoformat(datetime.datetime.now()) < user[10]
            if check:
                text = f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n<i>✨ VIP подписка активна до: {user[10]}</i>'
            else:
                text = (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                        f'<i>⚠  Подписка VIP просрочена</i>')
        else:
            text = (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                    f'<i>⚠  Для вывода средств необходимо оформить VIP подписку</i>')
        subscribe = await check_subscribe_db(user_id=call.message.chat.id)
        left = (datetime.datetime.fromisoformat(subscribe[1]).date() - datetime.datetime.now().date())
        text += f'\n<b>У вас осталось {left.days} дней подписки на бота\n</b>'
        await call.message.edit_text(text=text, reply_markup=await kb.user_menu(call.message.chat.id))
    else:
        await call.message.edit_text(text='<b>⛔  Подписка на бота закончилась!</b>\n<i>⚠  Для участия в играх необходи'
                                          'мо оформить подписку!</i>\n',
                                     reply_markup=await kb.admin_url_keyboard(status=False))
@callbacks.callback_query(F.data == 'user_prizes')
async def user_prizes(call: CallbackQuery):
    game = await get_active_game()
    if game:
        prizes_count = await get_prizes_count(game_id=game[0])
        text = (f'⚠  <i>Количество мест: {game[2]}\n'
                f'🎁  <b>Количество призовых мест: {prizes_count}</b></i>\n'
                f'✨  <b>Призы текущей игры:</b>\n\n')
        prizes = await get_prizes(game[0])
        for prize in prizes:
            text += f'<b>🎁  {prize[1]} - {prize[3]} шт.</b>\n'
        await call.message.edit_text(text=text,
                                     reply_markup=await kb.user_prizes_keyboard(prizes, call.message.chat.id, game[0]))
    else:
        await call.message.edit_text(text='⚠  Текущих игр нет', reply_markup=await kb.user_back_keyboard())
@callbacks.callback_query(F.data == 'user_subscribe')
async def user_subscribe(call: CallbackQuery):
    subscribe = await check_subscribe_db(user_id=call.message.chat.id)
    if subscribe[0]:
        days = datetime.datetime.fromisoformat(subscribe[1]) - datetime.datetime.now()
        await call.message.edit_text(text=f'<b>✅  Подписка на бота активна!</b>\n<i>✨  Осталось {days.days} '
                                          f'дней подписки</i>', reply_markup=await kb.user_back_keyboard())
    else:
        await call.message.edit_text(text='<b>⛔  Подписка на бота закончилась!</b>\n<i>⚠  Для участия в играх необход'
                                          'имо оформить подписку!</i>\n', reply_markup=await kb.admin_url_keyboard())

@callbacks.callback_query(F.data == 'admin_vip_subscribe')
async def admin_vip_subscribe(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Введите никнейм пользователя:', reply_markup=await kb.admin_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_username_to_update_vip)
@callbacks.callback_query(F.data == 'admin_bot_subscribe')
async def admin_bot_subscribe(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Введите никнейм пользователя:', reply_markup=await kb.admin_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_username_to_update_subscribe)
@callbacks.callback_query(F.data == 'admin_add_balance')
async def admin_add_balance(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Введите никнейм пользователя:', reply_markup=await kb.admin_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_username_to_update_balance)
@callbacks.callback_query(F.data == 'buy_vip')
async def buy_vip(call: CallbackQuery):
    await call.message.edit_text(text='<b>✨  Для приобретения подписки VIP, необходимо написать администратору</b>',
                                 reply_markup=await kb.admin_url_keyboard())
@callbacks.callback_query(F.data == 'buy_cash')
async def buy_vip(call: CallbackQuery):
    await call.message.edit_text(text='<b>✨  Для приобретения подписки VIP, необходимо написать администратору</b>',
                                 reply_markup=await kb.admin_url_keyboard())
@callbacks.callback_query(F.data == 'get_cash')
async def get_cash(call: CallbackQuery):
    if await check_vip(user_id=call.message.chat.id) == '':
        await call.message.edit_text(text='<b>✨  Для вывода средств, необходимо оформить VIP подписку</b>',
                                     reply_markup=await kb.admin_url_keyboard())
    await call.message.edit_text(text='<b>✨  Для вывода средств, необходимо написать администратору</b>',
                                 reply_markup=await kb.admin_url_keyboard())
@callbacks.callback_query(F.data == 'admin_edit_balance')
async def admin_edit_balance(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Введите никнейм пользователя:', reply_markup=await kb.admin_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_username_to_edit_balance)
@callbacks.callback_query(F.data == 'admin_u_b')
async def admin_u_b(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Введите сумму изменения баланса', reply_markup=await kb.admin_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_value_to_edit_balance)
@callbacks.callback_query(F.data == 'admin_s_b')
async def admin_s_b(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Введите сумму изменения баланса', reply_markup=await kb.admin_back_keyboard())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(FSM.set_value_to_update_balance)
@callbacks.callback_query(F.data.startswith('admin_send_'))
async def admin_send(call: CallbackQuery, state: FSMContext):
    await state.clear()
    send_id = int(call.data.split('_')[2])
    await call.message.delete()
    await admin_send_message(call.message, send_id)