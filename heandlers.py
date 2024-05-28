import asyncio
import datetime
import re
from contextlib import suppress
import random

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ChatPermissions, ChatJoinRequest, ChatMemberUpdated
from aiogram.filters import CommandStart, Command, CommandObject, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import ADMINS_IDS, START_BUTTONS, CHAT_PERMISSIONS, MOMENT_LOTO, MONTHLY_LOTO, WEEKLY_LOTO, DAILY_LOTO, \
    CHATS_IDS, SUB_NOTIF, KARMA_TIMEOUT, MODERATORS_IDS, GOODBYE_MESSAGE, LOTO_LIMIT
import keyboards as kb
from db import (register_user, check_subscribe_db, add_message, add_game, get_last_game, add_address,
                ban_user_db, unban_user_db, add_karma_db, get_user_by_username, update_subscribe,
                prize_update_text, prize_update_count, add_prize, get_prizes, get_prize, get_game_history,
                get_game_winners, get_user, get_game_users_count, get_game_winners_count, check_user, add_vip,
                update_balance, set_balance, get_game, get_usernames, get_today_messages, get_week_messages,
                get_month_messages, check_user_name, get_all_winners, get_winner_prizes, get_games_month,
                get_prizes_month, get_prizes_all, get_send_button, add_send_button, edit_button_text,
                edit_button_url, get_send_buttons, edit_send_media, edit_send_text, add_send, add_chat, get_chat,
                get_users_vip, get_users_novip, get_users, get_chats, get_send, add_scheduled_send, get_users_no_admin,
                delete_scheduled_send, edit_time_limit, get_request, get_goodbye, get_settings, set_settings,
                set_send_start_time, set_send_end_time)
from fsm import FSM

heandlers = Router()
async def admin_send_message(message: Message, send_id) -> Message:
    send = await get_send(send_id)
    buttons = await get_send_buttons(send_id)
    type = send[3]
    try:
        match type:
            case 'photo':
                if send[1]:
                    return await message.answer_photo(photo=send[2], caption=send[1][:4096],
                                               reply_markup=await kb.admin_send_keyboard(send_id, buttons))
                else:
                    return await message.answer_photo(photo=send[2],
                                                      reply_markup=await kb.admin_send_keyboard(send_id, buttons))

            case 'video':
                if send[1]:
                    return await message.answer_video(video=send[2], caption=send[1][:4096],
                                               reply_markup=await kb.admin_send_keyboard(send_id, buttons))
                else:
                    return await message.answer_video(video=send[2],
                                               reply_markup=await kb.admin_send_keyboard(send_id, buttons))

            case 'gif':
                if send[1]:
                    return await message.answer_animation(animation=send[2], caption=send[1][:4096],
                                                   reply_markup=await kb.admin_send_keyboard(send_id, buttons))
                else:
                    return await message.answer_animation(animation=send[2],
                                                   reply_markup=await kb.admin_send_keyboard(send_id, buttons))
            case 'text':
                return await message.answer(text=send[1][:4096],
                                            reply_markup=await kb.admin_send_keyboard(send_id, buttons))
            case _:
                return await message.answer(text='Ошибка отправки сообщения')
    except Exception as e:
        return await message.answer(text=f'{send[1][:3900]}\nПроизошла ошибка: {e}\nСообщение не будет отправлено',
                                    parse_mode='Markdown', reply_markup=await kb.admin_send_keyboard(send_id, buttons))
async def user_send_message(user_id, bot, send_id) -> Message | None:
    send = await get_send(send_id)
    buttons = await get_send_buttons(send_id)
    type = send[3]
    try:
        match type:
            case 'photo':
                if send[1]:
                    return await bot.send_photo(chat_id=user_id, photo=send[2], caption=send[1],
                                         reply_markup=await kb.user_send_keyboard(buttons))
                else:
                    return await bot.send_photo(chat_id=user_id, photo=send[2],
                                                reply_markup=await kb.user_send_keyboard(buttons))
            case 'video':
                if send[1]:
                    return await bot.send_video(chat_id=user_id, video=send[2], caption=send[1],
                                         reply_markup=await kb.user_send_keyboard(buttons))
                else:
                    return await bot.send_video(chat_id=user_id, video=send[2],
                                                reply_markup=await kb.user_send_keyboard(buttons))
            case 'gif':
                if send[1]:
                    return await bot.send_animation(chat_id=user_id, animation=send[2], caption=send[1],
                                             reply_markup=await kb.user_send_keyboard(buttons))
                else:
                    return await bot.send_animation(chat_id=user_id, animation=send[2],
                                             reply_markup=await kb.user_send_keyboard(buttons))
            case 'text':
                return await bot.send_message(chat_id=user_id, text=send[1],
                                              reply_markup=await kb.user_send_keyboard(buttons))
    except Exception:
        return None
async def is_admin(message: Message):
    if message.from_user.id in ADMINS_IDS:
        return True
    return False
async def is_moderator(message: Message):
    if message.from_user.id in MODERATORS_IDS:
        return True
    return False
async def is_chat_member(message: Message, bot: Bot):
    not_chat_member = []
    if START_BUTTONS:
        for button in START_BUTTONS:
            try:
                button['chat_id'] = int(button['chat_id'])
            except TypeError:
                print(f'ОШИБКА: неправильный ID чата в кнопке {button["button_text"]} в файле config.py')
                for admin in ADMINS_IDS:
                    await bot.send_message(chat_id=admin, text=f'ОШИБКА: неправильный ID чата в кнопке'
                                                               f' {button["button_text"]} в файле config.py')
            subscribe = await bot.get_chat_member(chat_id=button['chat_id'], user_id=message.chat.id)
            if not subscribe.status or subscribe.status == 'left' or subscribe.status == 'kicked':
                not_chat_member.append(button)
        return not_chat_member
    else:
        return []
async def interval_sending(users, send_id, bot: Bot):
    send = await get_send(send_id)
    if send[4]:
        match_ = re.match(r'(\d{2}):(\d{2})', send[4])
        if datetime.datetime.now() <= datetime.datetime.now().replace(hour=int(match_.group(1)), minute=int(match_.group(2))):
            return
    if send[5]:
        match1 = re.match(r'(\d{2}):(\d{2})', send[5])
        if datetime.datetime.now() >= datetime.datetime.now().replace(hour=int(match1.group(1)), minute=int(match1.group(2))):
            return
    for user in users:
        await user_send_message(user_id=user[0], bot=bot, send_id=send_id)
async def later_sending(users, send_id, bot: Bot, sched_id):
    for user in users:
        await user_send_message(user_id=user[0], bot=bot, send_id=send_id)
    await delete_scheduled_send(sched_id=sched_id)
@heandlers.message(FSM.set_send_starttime)
async def set_send_starttime(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    try:
        match_ = re.match(r'(\d{2}):(\d{2})', message.text)
        time = datetime.datetime.now().replace(hour=int(match_.group(1)), minute=int(match_.group(2))).strftime('%H:%M')
    except ValueError:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                    text='Введите корректное время в формате ЧЧ:ММ',
                                    reply_markup=await kb.admin_back_to_interval_keyboard())
        await state.set_state(FSM.set_send_starttime)
        return
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Время начала отправки установлено на: {message.text}',
                                reply_markup=await kb.admin_back_to_interval_keyboard())
    await set_send_start_time(data['send_id'], time)

@heandlers.message(FSM.set_send_endtime)
async def set_send_endtime(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    try:
        match_ = re.match(r'(\d{2}):(\d{2})', message.text)
        time = datetime.datetime.now().replace(hour=int(match_.group(1)), minute=int(match_.group(2))).strftime('%H:%M')
    except ValueError:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                    text='Введите корректное время в формате ЧЧ:ММ',
                                    reply_markup=await kb.admin_back_to_interval_keyboard())
        await state.set_state(FSM.set_send_endtime)
        return
    await state.update_data(end_time=time)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Время окончания отправки установлено на: {message.text}',
                                reply_markup=await kb.admin_back_to_interval_keyboard())
    await set_send_end_time(data['send_id'], time)
@heandlers.message(FSM.set_moment_min)
async def set_moment_min(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    try:
        value = float(message.text)
    except ValueError:
        await bot.edit_message_text(chat_id=message.chat.id, text='Введите число', message_id=data['message_id'],
                               reply_markup=await kb.admin_back_to_loto_settings_keyboard())
        await state.set_state(FSM.set_moment_min)
        return
    LOTO_LIMIT[0] = value
    await bot.edit_message_text(chat_id=message.chat.id,
                                text=f'Минимальное значение моментальной лотереи установлено на {value}',
                           message_id=data['message_id'], reply_markup=await kb.admin_back_to_loto_settings_keyboard())
    await state.clear()
@heandlers.message(FSM.set_moment_max)
async def set_moment_max(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    try:
        value = float(message.text)
    except ValueError:
        await bot.edit_message_text(chat_id=message.chat.id, text='Введите число', message_id=data['message_id'],
                               reply_markup=await kb.admin_back_to_loto_settings_keyboard())
        await state.set_state(FSM.set_moment_max)
        return
    LOTO_LIMIT[1] = value
    await bot.edit_message_text(chat_id=message.chat.id,
                                text=f'Максимальное значение моментальной лотереи установлено на {value}',
                           message_id=data['message_id'], reply_markup=await kb.admin_back_to_loto_settings_keyboard())
    await state.clear()

@heandlers.chat_join_request()
async def chat_join_request(request: ChatJoinRequest):
    if await get_request():
        if (await get_request())[0] == 1:
            await request.approve()
@heandlers.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def leave_chat(update: ChatMemberUpdated, bot: Bot):
    if await get_goodbye():
        if (await get_goodbye())[0] == 1:
            await bot.send_message(chat_id=update.from_user.id,
                                   text=f'<b>Вы покинули чат {update.chat.title}!\n{GOODBYE_MESSAGE}</b>',
                                   reply_markup=await kb.leave_chat_keyboard((
                                        await bot.create_chat_invite_link(chat_id=update.chat.id)).invite_link))
@heandlers.message(FSM.set_answer_text)
async def set_answer_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(text=message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    user = await get_user(data['user_id'])
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=
                                f'Отправить сообщение:\n{message.text}\nпользователю {user[1] if user[1] else user[2]}?',
                                reply_markup=await kb.admin_accept_answer_keyboard(data["sender_id"]))
@heandlers.message(FSM.set_user_message_text)
async def set_user_message_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(text=message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id, text=f'💬  <b>Отправить сообщение:<i>\n{message.text}?</i></b>',
                                reply_markup=await kb.user_accept_message_keyboard(), message_id=data['message_id'])
@heandlers.message(FSM.set_user_reply_text)
async def set_user_reply_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(text=message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id, text=f'💬  <b>Отправить сообщение:<i>\n{message.text}?</i></b>',
                                reply_markup=await kb.user_accept_reply_keyboard(), message_id=data['message_id'])
@heandlers.message(FSM.set_moderator_id)
async def set_moderator_id(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(moderator=message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if not await check_user(username=data['moderator']):
        await bot.edit_message_text(chat_id=message.chat.id, text='Пользователь не найден', message_id=data['message_id'],
                                    reply_markup=await kb.admin_back_to_moderators_keyboard())
        await state.set_state(FSM.set_moderator_id)
        return
    user = await get_user_by_username(username=data['moderator'])
    await state.update_data(user_id=user[0])
    await bot.edit_message_text(chat_id=message.chat.id, text='Подтвердить добавление модератора?',
                           reply_markup=await kb.admin_accept_moderator_keyboard(), message_id=data['message_id'])
@heandlers.message(FSM.set_value_donate)
async def set_value_donate(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    try:
        value = float(message.text)
    except ValueError:
        await bot.edit_message_text(chat_id=message.chat.id, text='✏ <b> Введите число</b>',
                                    message_id=data['message_id'], reply_markup=await kb.user_back_keyboard())
        await state.set_state(FSM.set_value_donate)
        return
    if value < 1 or value > (await get_user(message.chat.id))[9]:
        await bot.edit_message_text(chat_id=message.chat.id, text='✏  <b>Введите корректное значение</b>',
                                    message_id=data['message_id'], reply_markup=await kb.user_back_keyboard())
        await state.set_state(FSM.set_value_donate)
        return
    await state.update_data(value=value)
    await bot.edit_message_text(chat_id=message.chat.id, text='💸 <b> Подтвердить добавление суммы?</b>',
                           reply_markup=await kb.user_accept_donate_keyboard(), message_id=data['message_id'])
@heandlers.message(FSM.set_antispam_value)
async def set_antispam_value(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    try:
        value = float(message.text)
    except ValueError:
        await bot.edit_message_text(chat_id=message.chat.id, text='✏ <b> Введите число</b>',
                                    message_id=data['message_id'],
                                    reply_markup=await kb.admin_back_to_antispam_keyboard())
        await state.set_state(FSM.set_antispam_value)
        return
    if value < 0:
        await bot.edit_message_text(chat_id=message.chat.id, text='✏  <b>Введите корректное значение</b>',
                                    message_id=data['message_id'],
                                    reply_markup=await kb.admin_back_to_antispam_keyboard())
        await state.set_state(FSM.set_antispam_value)
        return
    await edit_time_limit(value)
    await bot.edit_message_text(chat_id=message.chat.id, text=f'Установлено новое значение антиспама: {value}',
                           reply_markup=await kb.admin_back_to_antispam_keyboard(), message_id=data['message_id'])
    await state.clear()
@heandlers.message(Command(commands=['add_chat']))
async def add_chat_(message: Message, bot: Bot):
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except TelegramBadRequest:
        pass
    if await is_admin(message):
        if await get_chat(chat_id=message.chat.id):
            return
        await add_chat(chat_id=message.chat.id, chat_name=message.chat.title)
        msg = await bot.send_message(chat_id=message.from_user.id, text='Чат успешно добавлен в базу данных')
        await asyncio.sleep(5)
        await bot.delete_message(chat_id=message.from_user.id, message_id=msg.message_id)
    return
@heandlers.message(FSM.set_send_interval)
async def set_send_interval(message: Message, state: FSMContext, bot: Bot, scheduler: AsyncIOScheduler):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    interval, users = 0, []
    try:
        match_ = re.match(r'(\d+)\s?([А-яA-z])', message.text)
        interval = int(match_.group(1))
        if interval < 1:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                        text='Введите число больше 0',
                                        reply_markup=await kb.admin_back_to_sends_keyboard())
            await state.set_state(FSM.set_send_interval)
            return
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
            case _:
                await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                            text='Введите корректное значение интервала времени',
                                            reply_markup=await kb.admin_back_to_sends_keyboard())
    except ValueError:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                    text='Введите число с единицей измерения (м, ч, д, н)',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_send_interval)
        return
    await state.clear()
    match data["target"]:
        case "vip":
            users = await get_users_vip()
        case "novip":
            users = await get_users_novip()
        case "all":
            users = await get_users_no_admin(ADMINS_IDS)
        case "chat":
            users = await get_chats()
    sched = await add_scheduled_send(send_id=data["send_id"], target=data["target"], time=message.text, type='interval')
    scheduler.add_job(func=interval_sending, trigger='interval', minutes=interval, id=f'{sched[4]}',
                      kwargs={'users': users, 'send_id': data['send_id'], 'bot': bot})
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id_2'],
                                text='Рассылка успешно добавлена', reply_markup=await kb.admin_back_to_sends_keyboard())
    await bot.delete_message(chat_id=message.chat.id, message_id=data['message_id_1'])
@heandlers.message(FSM.set_send_time)
async def set_send_time(message: Message, state: FSMContext, bot: Bot, scheduler: AsyncIOScheduler):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    time = message.text
    users = []
    match data["target"]:
        case "vip":
            users = await get_users_vip()
        case "novip":
            users = await get_users_novip()
        case "all":
            users = await get_users()
        case "chat":
            users = await get_chats()
    try:
        time = datetime.datetime.fromisoformat(time)
    except ValueError as err:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                    text='Введите корректное время в формате ГГГГ-ММ-ДД ЧЧ:ММ',
                                    reply_markup=await kb.admin_back_to_sends_keyboard())
        await state.set_state(FSM.set_send_time)
        return
    sched = await add_scheduled_send(send_id=data["send_id"], target=data["target"], time=time, type='time')
    scheduler.add_job(func=later_sending, trigger='date', id=f'{sched[4]}', run_date=time,
                      kwargs={'users': users, 'send_id': data['send_id'], 'bot': bot, 'sched_id': sched[4]})
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id_2'],
                                text='Рассылка успешно добавлена', reply_markup=await kb.admin_back_to_sends_keyboard())
    await bot.delete_message(chat_id=message.chat.id, message_id=data['message_id_1'])
    await state.clear()

@heandlers.message(FSM.set_new_button_text)
async def set_new_button_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await edit_button_text(button_id=data['button_id'], text=message.text)
    button = await get_send_button(button_id=data['button_id'])
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Текст кнопки успешно изменён на {message.text}\n{button[3]}',
                                reply_markup=await kb.admin_button_keyboard(button=button))
    await state.clear()
@heandlers.message(FSM.set_new_button_url)
async def set_new_button_url(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await edit_button_url(button_id=data['button_id'], url=message.text)
    button = await get_send_button(button_id=data['button_id'])
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Ссылка кнопки успешно изменена на {message.text}',
                                reply_markup=await kb.admin_button_keyboard(button=button))
    await state.clear()
@heandlers.message(FSM.set_button_text)
async def set_button_text(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(button_text=message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите ссылку кнопки',
                                reply_markup=await kb.admin_back_to_send_keyboard(data["send_id"]))
    await state.set_state(FSM.set_button_url)
@heandlers.message(FSM.set_button_url)
async def set_button_url(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    await add_send_button(send_id=data['send_id'], text=data['button_text'], url=message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    buttons = await get_send_buttons(send_id=data['send_id'])
    await bot.edit_message_text(chat_id=message.chat.id, text='Кнопка успешно добавлена', message_id=data['message_id'],
                           reply_markup=await kb.admin_back_to_send_keyboard(data['send_id']))
@heandlers.message(FSM.set_send_text)
async def set_send_text(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if len(message.text) > 1024:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text='⚠  Слишком длинное сообщение, максимальная длина - 1024 символа',
                               reply_markup=await kb.admin_back_to_sends_keyboard())
        await state.set_state(FSM.set_send_text)
        return
    await state.update_data(text=message.text)
    await bot.edit_message_text(chat_id=message.chat.id, text='Отправьте медиафайл', message_id=data['message_id'],
                                reply_markup=await kb.admin_send_media_keyboard())
    await state.set_state(FSM.set_send_media)
@heandlers.message(FSM.set_send_media)
async def set_send_media(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if message.photo:
        media = message.photo[-1].file_id
        type = 'photo'
    elif message.video:
        media = message.video.file_id
        type = 'video'
    elif message.animation:
        media = message.animation.file_id
        type = 'gif'
    else:
        await bot.send_message(chat_id=message.chat.id, reply_markup=await kb.admin_back_to_sends_keyboard(),
                               text='⚠  Неправильный формат, отправьте медиафайл ещё раз в другом формате')
        await state.set_state(FSM.set_send_media)
        return
    await add_send(text=data['text'], media=media, type=type)
    data = await state.get_data()
    await bot.edit_message_text(chat_id=message.chat.id, text='Сообщение успешно добавлено',
                                message_id=data['message_id'], reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.clear()
@heandlers.message(FSM.set_new_send_media)
async def set_new_send_media(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if message.photo:
        media = message.photo[-1].file_id
        type = 'photo'
    elif message.video:
        media = message.video.file_id
        type = 'video'
    elif message.animation:
        media = message.animation.file_id
        type = 'gif'
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='⚠  Неправильный формат, отправьте медиафайл ещё раз в другом формате',
                                    reply_markup=await kb.admin_back_to_send_keyboard(data['send_id']))
        await state.set_state(FSM.set_new_send_media)
        return
    await edit_send_media(send_id=data['send_id'], media=media, type=type)
    await bot.send_message(chat_id=message.chat.id, text='Медиафайл успешно изменён',
                           reply_markup=await kb.admin_back_to_send_keyboard(data['send_id']))
    await state.clear()
@heandlers.message(FSM.set_new_send_text)
async def set_new_send_text(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if len(message.text) > 1024:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text='⚠  Слишком длинное сообщение, максимальная длина - 1024 символа',
                               reply_markup=await kb.admin_back_to_sends_keyboard())
        await state.set_state(FSM.set_new_send_text)
        return
    await edit_send_text(send_id=data['send_id'], text=message.text)
    await bot.edit_message_text(text='Текст сообщения успешно изменён', message_id=data['message_id'],
                                chat_id=message.chat.id,
                                reply_markup=await kb.admin_back_to_send_keyboard(data['send_id']))
    await state.clear()
@heandlers.message(FSM.add_send_photo)
async def add_send_photo(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if message.photo:
        media = message.photo[-1].file_id
        type = 'photo'
    elif message.video:
        media = message.video.file_id
        type = 'video'
    elif message.animation:
        media = message.animation.file_id
        type = 'gif'
    else:
        await bot.edit_message_text(chat_id=message.chat.id, reply_markup=await kb.admin_back_to_sends_keyboard(),
                               text='⚠  Неправильный формат, отправьте медиафайл ещё раз в другом формате',
                                    message_id=data['message_id'])
        await state.set_state(FSM.add_send_photo)
        return
    await edit_send_media(send_id=data['send_id'], media=media, type=type)
    await bot.edit_message_text(chat_id=message.chat.id, text='Медиа успешно добавлено', message_id=data['message_id'],
                           reply_markup=await kb.admin_back_to_send_keyboard(send_id=data['send_id']))
    await state.clear()
async def captcha(message: Message, bot: Bot):
    list = ['🍇', '🍒', '🥭', '🍋', '🍉', '1🍓']
    random.shuffle(list)
    await bot.send_message(chat_id=message.chat.id, text='👁‍🗨  <b>Для начала работы с ботом пройдите капчу: '
                                                         'нажмите на клубнику</b>',
                           reply_markup=await kb.captcha_keyboard(list))
@heandlers.message(CommandStart())
async def start(message: Message, bot: Bot, state: FSMContext, captcha_check: bool = False):
    referrer = message.text[7:]
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if not await get_settings():
        await set_settings()
    if data:
        pass
    else:
        await state.update_data(referrer=referrer)
    if message.chat.type != 'private':
        return
    if await is_moderator(message):
        await register_user(user_id=message.chat.id, first_name=message.chat.first_name,
                            username=message.chat.username, referrer=referrer)
        game = await get_last_game()
        if game is None:
            active = 2
        else:
            active = game[4]
        await message.answer(text='Меню модератора', reply_markup=await kb.moderator_keyboard(active=active))
        return
    if await is_admin(message=message):
        await register_user(user_id=message.chat.id, first_name=message.chat.first_name,
                            username=message.chat.username, referrer=referrer)
        game = await get_last_game()
        if game is None:
            active = 2
        else:
            active = game[4]
        await message.answer(text='Меню администратора:', reply_markup=await kb.admin_keyboard(active=active))
        return
    else:
        if captcha_check == False:
            await captcha(message=message, bot=bot)
            return
        buttons = await is_chat_member(message=message, bot=bot)
        if not buttons:
            data = await state.get_data()
            referrer = data['referrer']
            if referrer != '':
                try:
                    referrer = int(referrer)
                except ValueError:
                    referrer = None
                    await bot.send_message(chat_id=message.chat.id, text='Ошибка в ссылке реферала')
            else:
                referrer = None
            await state.clear()
            if referrer == message.chat.id or referrer == message.from_user.id:
                referrer = None
            if await register_user(user_id=message.chat.id, first_name=message.chat.first_name,
                                   username=message.chat.username, referrer=referrer):
                user = await get_user(user_id=message.chat.id)
                text = (f'<b>✨  Добро пожаловать, {message.chat.first_name}!, вам автоматически предоставлена '
                        f'подписка на 7 дней\n</b>')
                if SUB_NOTIF:
                    for chat in CHATS_IDS:
                        await bot.send_message(chat_id=chat, text=f'<b>📢  Пользователь @{message.chat.username} '
                                                                  f'присоединился к нам!</b>')
                if user[10] != '':
                    check = datetime.datetime.isoformat(datetime.datetime.now()) < user[10]
                    if check:
                        text += (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                                 f'<i>✨ VIP подписка активна до: {user[10]}</i>')
                    else:
                        text += (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                                f'<i>⚠  Подписка VIP просрочена</i>')
                else:
                    text += (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                            f'<i>⚠  Для вывода средств необходимо оформить VIP подписку</i>')
                markup = await kb.user_menu(message.chat.id)
                if referrer is not None:
                    await bot.send_message(chat_id=referrer, text=f'✅  Пользователь @{message.chat.username} перешёл '
                                                                  f'по вашей ссылке',
                                           reply_markup=await kb.user_menu(referrer))
            else:
                user = await get_user(user_id=message.chat.id)
                subscribe = await check_subscribe_db(user_id=message.chat.id)
                if subscribe[0]:
                    left = (datetime.datetime.fromisoformat(subscribe[1]).date() - datetime.datetime.now().date())
                    text = (f'<b>✨  Добро пожаловать, {message.chat.first_name} ! \nУ вас осталось {left.days} дней '
                            f'подписки на бота\n</b>')
                    if user[10] != '':
                        check = datetime.datetime.isoformat(datetime.datetime.now()) < user[10]
                        if check:
                            text += (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                                     f'<i>✨ VIP подписка активна до: {user[10]}</i>')
                        else:
                            text += (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                                     f'<i>⚠  Подписка VIP просрочена</i>')
                    else:
                        text += (f'📋  <b>Меню:</b>\n<b>💵  Баланс: {user[9]}</b>\n'
                                 f'<i>⚠  Для вывода средств необходимо оформить VIP подписку</i>')
                    markup = await kb.user_menu(message.chat.id)
                else:
                    markup = await kb.admin_url_keyboard()
                    text = f'Добро пожаловать, {message.chat.first_name} ! \nУ вас закончилась подписка на бота'
            await message.answer(text=text, reply_markup=markup)
        else:
            await message.answer(text='Для использования бота необxодима подписка на:',
                                 reply_markup=await kb.start_keyboard(buttons=buttons))
@heandlers.message(FSM.set_moment_loto_value)
async def set_moment_loto_value(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        value = float(message.text)
        user = await get_user(user_id=message.from_user.id)
        if value > user[9]:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Сумма ставки '
                                        'превышает ваш баланс', reply_markup=await kb.user_back_keyboard())
            await state.set_state(FSM.set_moment_loto_value)
            return
        if value < LOTO_LIMIT[0] or value > LOTO_LIMIT[1]:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Сумма ставки '
                                        f'вышла за допустимые лимиты\n<b>Ограничения по ставкам: от {LOTO_LIMIT[0]} до '
                                        f'{LOTO_LIMIT[1]}\n</b>', reply_markup=await kb.user_back_keyboard())
            await state.set_state(FSM.set_moment_loto_value)
            return
    except ValueError:
        await bot.edit_message_text(message_id=data['message_id'], chat_id=message.from_user.id,
                                    text='⚠  Введите число', reply_markup=await kb.user_back_keyboard())
        await state.set_state(FSM.set_moment_loto_value)
        return
    await state.update_data(value=value)
    await bot.edit_message_text(chat_id=message.from_user.id, text=f'✅  Подтвердить ставку на сумму: {value}',
                           reply_markup=await kb.moment_loto_value_keyboard(), message_id=data['message_id'])
@heandlers.message(Command(commands=['get_chat_id']))
async def get_chat_id(message: Message, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if await is_admin(message):
        await bot.send_message(chat_id=message.from_user.id, text=f'ID выбранного чата:\n{message.chat.id}')
@heandlers.message(FSM.set_message_user)
async def set_message_user(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = await get_user_by_username(username=message.text)
    if not user_id:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                    text='Пользователь не найден попробуйте ещё раз',
                                    reply_markup=await kb.admin_back_to_sends_keyboard())
        await state.set_state(FSM.set_message_user)
        return
    user = await get_user(user_id=user_id[0])
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if not user:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                    text='Пользователь не найден попробуйте ещё раз',
                                    reply_markup=await kb.admin_back_to_sends_keyboard())
        await state.set_state(FSM.set_message_user)
        return
    await state.update_data(user_id=user[0], username=message.text)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Введите сообщение пользователю {user[1] if user[1] else user[2]}',
                                reply_markup=await kb.admin_back_to_sends_keyboard())
    await state.set_state(FSM.set_message_text)
    return
@heandlers.message(FSM.set_message_text)
async def set_message_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(text=message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Отправить сообщение:\n{message.text}\nпользователю {data["username"]}?',
                                reply_markup=await kb.admin_accept_message_keyboard())
@heandlers.message(FSM.set_game_name)
async def set_game_name(message: Message, state: FSMContext, bot: Bot):
    game_name = message.text
    await message.delete()
    await state.update_data(game_name=game_name)
    data = await state.get_data()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text='Введите количество игроков', reply_markup=await kb.admin_new_game())
    await state.set_state(FSM.set_number_of_users)
@heandlers.message(FSM.set_number_of_users)
async def set_number_of_users(message: Message, state: FSMContext, bot: Bot):
    try:
        number_of_users = int(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_number_of_users)
        return
    await state.update_data(number_of_users=number_of_users)
    data = await state.get_data()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text='Введите количество победителей', reply_markup=await kb.admin_new_game())
    await state.set_state(FSM.set_number_of_winners)
@heandlers.message(FSM.set_number_of_winners)
async def set_number_of_winners(message: Message, state: FSMContext, bot: Bot):
    try:
        number_of_winners = int(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_number_of_winners)
        return
    data = await state.get_data()
    game_name = data['game_name']
    number_of_users = data['number_of_users']
    await state.clear()
    await add_game(users_count=number_of_users, winners_count=number_of_winners, game_name=game_name)
    game = await get_last_game()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Игра "{game_name}" успешно добавлена в базу данных',
                                reply_markup=await kb.current_game_keyboard(game=game))
@heandlers.message(FSM.set_moment_loto_chance)
async def set_moment_loto_chance(message: Message, state: FSMContext, bot: Bot):
    try:
        chance = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_moment_loto_chance)
        return
    MOMENT_LOTO[0] = chance
    data = await state.get_data()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text='Шанс победы успешно изменён',
                                reply_markup=await kb.admin_moment_loto_settings_keyboard())
@heandlers.message(FSM.set_moment_loto_coefficient)
async def set_moment_loto_coefficient(message: Message, state: FSMContext, bot: Bot):
    try:
        coefficient = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_moment_loto_coefficient)
        return
    data = await state.get_data()
    await state.clear()
    MOMENT_LOTO[1] = coefficient
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Коэффициент умножения ставки успешно изменен',
                                reply_markup=await kb.admin_moment_loto_settings_keyboard())
@heandlers.message(FSM.set_daily_loto_value)
async def set_daily_loto_value(message: Message, state: FSMContext, bot: Bot):
    try:
        value = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_daily_loto_value)
        return
    data = await state.get_data()
    await state.clear()
    DAILY_LOTO[0] = value
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Сумма стартовой ставки успешно изменена на {value}\n'
                                     f'<b>Настройки ежемесячной лотереи:\nТекущие настройки:</b>\nСтартовая сумма: '
                                     f'<i>{DAILY_LOTO[0]}\nКоэффициент умножения: {DAILY_LOTO[1]}</i>',
                                reply_markup=await kb.admin_daily_loto_settings_keyboard())
@heandlers.message(FSM.set_username_to_send_cash)
async def set_username_to_send_cash(message: Message, state: FSMContext, bot: Bot):
    username = message.text
    data = await state.get_data()
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if not await check_user_name(username) and not await check_user(username):
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='<i>🔍  Пользователь '
                                    'не найден\n</i>📲  <b>Введите никнейм пользователя для отправки денежных средств:'
                                    '</b>', reply_markup=await kb.user_back_keyboard())
        await state.set_state(FSM.set_username_to_send_cash)
        return
    await state.update_data(username=username)
    await state.set_state(FSM.set_value_to_send_cash)
    data = await state.get_data()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text='Введите сумму для перевода', reply_markup=await kb.user_back_keyboard())
@heandlers.message(FSM.set_value_to_send_cash)
async def set_value_to_send_cash(message: Message, state: FSMContext, bot: Bot):
    value = message.text
    try:
        value = float(value)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Введите число',
                                    reply_markup=await kb.user_back_keyboard())
        await state.set_state(FSM.set_value_to_send_cash)
        return
    data = await state.get_data()
    await update_balance(user_id=message.from_user.id, value=-value)
    user = await check_user(username=data['username']) or await check_user_name(name=data['username'])
    await update_balance(user_id=user[0], value=value)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text=f'✅  Сумма {value} успе'
                                f'шно переведена пользователю {user[2]}', reply_markup=await kb.user_back_keyboard())
    await bot.send_message(chat_id=user[0], text=f'✅  Вам была переведена сумма {value} от пользователя '
                           f'{message.from_user.username}', reply_markup=await kb.user_back_keyboard())
    await state.clear()
@heandlers.message(FSM.set_daily_loto_coefficient)
async def set_daily_loto_coefficient(message: Message, state: FSMContext, bot: Bot):
    try:
        coefficient = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_daily_loto_coefficient)
        return
    data = await state.get_data()
    await state.clear()
    DAILY_LOTO[1] = coefficient
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Коэффициент умножения ставки успешно изменен на {coefficient}\n'
                                     f'<b>Настройки ежемесячной лотереи:\nТекущие настройки:</b>\nСтартовая сумма: '
                                     f'<i>{DAILY_LOTO[0]}\nКоэффициент умножения: {DAILY_LOTO[1]}</i>',
                                reply_markup=await kb.admin_daily_loto_settings_keyboard())
@heandlers.message(FSM.set_weekly_loto_value)
async def set_weekly_loto_value(message: Message, state: FSMContext, bot: Bot):
    try:
        value = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_weekly_loto_value)
        return
    data = await state.get_data()
    await state.clear()
    WEEKLY_LOTO[0] = value
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Сумма стартовой ставки успешно изменена на {value}\n'
                                     f'<b>Настройки ежемесячной лотереи:\nТекущие настройки:</b>\nСтартовая сумма: '
                                     f'<i>{WEEKLY_LOTO[0]}\nКоэффициент умножения: {WEEKLY_LOTO[1]}</i>',
                                reply_markup=await kb.admin_weekly_loto_settings_keyboard())
@heandlers.message(FSM.set_weekly_loto_coefficient)
async def set_weekly_loto_coefficient(message: Message, state: FSMContext, bot: Bot):
    try:
        coefficient = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_weekly_loto_coefficient)
        return
    data = await state.get_data()
    await state.clear()
    WEEKLY_LOTO[1] = coefficient
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Коэффициент умножения ставки успешно изменен на {coefficient}\n'
                                     f'<b>Настройки ежемесячной лотереи:\nТекущие настройки:</b>\nСтартовая сумма: '
                                     f'<i>{WEEKLY_LOTO[0]}\nКоэффициент умножения: {WEEKLY_LOTO[1]}</i>',
                                reply_markup=await kb.admin_weekly_loto_settings_keyboard())
@heandlers.message(FSM.set_monthly_loto_value)
async def set_monthly_loto_value(message: Message, state: FSMContext, bot: Bot):
    try:
        value = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_monthly_loto_value)
        return
    data = await state.get_data()
    await state.clear()
    MONTHLY_LOTO[0] = value
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Сумма стартовой ставки успешно изменена на {value}\n'
                                     f'<b>Настройки ежемесячной лотереи:\nТекущие настройки:</b>\nСтартовая сумма: '
                                     f'<i>{MONTHLY_LOTO[0]}\nКоэффициент умножения: {MONTHLY_LOTO[1]}</i>',
                                reply_markup=await kb.admin_monthly_loto_settings_keyboard())
@heandlers.message(FSM.set_monthly_loto_coefficient)
async def set_monthly_loto_coefficient(message: Message, state: FSMContext, bot: Bot):
    try:
        coefficient = float(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Введите число',
                                    reply_markup=await kb.admin_new_game())
        await state.set_state(FSM.set_monthly_loto_coefficient)
        return
    data = await state.get_data()
    await state.clear()
    MONTHLY_LOTO[1] = coefficient
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text=f'Коэффициент умножения ставки успешно изменен на {coefficient}\n'
                                     f'<b>Настройки ежемесячной лотереи:\nТекущие настройки:</b>\nСтартовая сумма: '
                                     f'<i>{MONTHLY_LOTO[0]}\nКоэффициент умножения: {MONTHLY_LOTO[1]}</i>',
                                reply_markup=await kb.admin_monthly_loto_settings_keyboard())

@heandlers.message(FSM.set_address)
async def set_address(message: Message, state: FSMContext, bot: Bot):
    address = message.text
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    await add_address(address=address)
    await state.clear()
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                                text='Промокод добавлен', reply_markup=await kb.admin_new_game())
@heandlers.message(FSM.set_username_to_update_subscribe)
async def set_username_to_update_subscribe(message: Message, state: FSMContext, bot: Bot):
    username = message.text
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if not await check_user(username) and not await check_user_name(username):
        message_id = data['message_id']
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                    text='Пользователь не найден, попробуйте ещё раз',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_username_to_update_subscribe)
        return
    await state.update_data(username=username)
    data = await state.get_data()
    message_id = data['message_id']
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                text='🗓  Введите количество дней подписки на бота',
                                reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_days_of_subscribe)
@heandlers.message(FSM.set_username_to_update_vip)
async def set_username_to_update_vip(message: Message, state: FSMContext, bot: Bot):
    username = message.text
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if not await check_user(username) and not await check_user_name(username):
        message_id = data['message_id']
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                    text='Пользователь не найден, попробуйте ещё раз',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_username_to_update_vip)
        return
    await state.update_data(username=username)
    data = await state.get_data()
    message_id = data['message_id']
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                text='🗓  Введите количество дней подписки ',
                                reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_days_of_subscribe_vip)
@heandlers.message(FSM.set_username_to_update_balance)
async def set_username_to_update_vip(message: Message, state: FSMContext, bot: Bot):
    username = message.text
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if not await check_user(username) and not await check_user_name(username):
        message_id = data['message_id']
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                    text='Пользователь не найден, попробуйте отправить username ещё раз',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_username_to_update_balance)
        return
    await state.update_data(username=username)
    data = await state.get_data()
    message_id = data['message_id']
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                text='💵  Введите сумму пополнения ', reply_markup=await kb.admin_back_keyboard())
    await state.set_state(FSM.set_new_balance)
@heandlers.message(FSM.set_new_balance)
async def set_new_balance(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    try:
        balance = float(message.text)
        data = await state.get_data()
        username = data['username']
        if username[0] == '@':
            username = username[1:]
        user = await get_user_by_username(username) and await check_user_name(username)
        await update_balance(user_id=user[0], value=balance)
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text=f'Баланс пользователя @{username} успешно пополнен на {balance}',
                                    reply_markup=await kb.admin_back_keyboard())
        await bot.send_message(chat_id=user[0], text=f'<b>✅  Ваша баланс пополнен на {balance}!</b>',
                               reply_markup=await kb.user_back_keyboard())
        await state.clear()
    except ValueError:
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Введите число',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_days_of_subscribe)
        return
@heandlers.message(FSM.set_days_of_subscribe)
async def set_days_of_subscribe(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    try:
        days = int(message.text)
        data = await state.get_data()
        username = data['username']
        if username[0] == '@':
            username = username[1:]
        user = await get_user_by_username(username) or await check_user_name(username)
        await update_subscribe(user_id=user[0], subscribe_left=days)
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text=f'Подписка на бота пользователя @{username} продлена на {days} дней',
                                    reply_markup=await kb.admin_back_keyboard())
        await bot.send_message(chat_id=user[0], text=f'<b>✅  Ваша подписка на бота продлена на {days} дней!</b>',
                               reply_markup=await kb.user_back_keyboard())
        await state.clear()
    except ValueError:
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Введите число',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_days_of_subscribe)
        return
@heandlers.message(FSM.set_days_of_subscribe_vip)
async def set_days_of_subscribe_vip(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    try:
        days = int(message.text)
        data = await state.get_data()
        username = data['username']
        if username[0] == '@':
            username = username[1:]
        user = await get_user_by_username(username) or await check_user_name(username)
        await add_vip(user_id=user[0], value=days)
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text=f'Подписка VIP пользователя @{username} продлена на {days} дней',
                                    reply_markup=await kb.admin_back_keyboard())
        await bot.send_message(chat_id=user[0], text=f'<b>✅  Ваша VIP подписка продлена на {days} дней!</b>',
                               reply_markup=await kb.user_back_keyboard())
        await state.clear()
    except ValueError:
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Введите число',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_days_of_subscribe_vip)
        return
@heandlers.message(FSM.set_username_to_edit_balance)
async def set_username_to_edit_balance(message: Message, state: FSMContext, bot: Bot):
    username = message.text
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    if not await check_user(username) and not await check_user_name(username):
        message_id = data['message_id']
        await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                    text='Пользователь не найден, попробуйте отправить username ещё раз',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_username_to_edit_balance)
        return
    await state.update_data(username=username)
    data = await state.get_data()
    message_id = data['message_id']
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id,
                                text='Выберите вариант: ', reply_markup=await kb.admin_update_balance_keyboard())
    await state.set_state(FSM.set_value_to_edit_balance)
@heandlers.message(FSM.set_value_to_edit_balance)
async def set_value_to_edit_balance(message: Message, state: FSMContext, bot: Bot):
    value = message.text
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    try:
        value = float(value)
    except ValueError:
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Введите число',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_value_to_edit_balance)
        return
    data = await state.get_data()
    username = data['username']
    if username[0] == '@':
        username = username[1:]
    user = await get_user_by_username(username) or await check_user_name(username)
    await update_balance(user_id=user[0], value=value)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text=f'Баланс пользователя @{username} успешно изменён на {value}',
                                reply_markup=await kb.admin_back_keyboard())
    await bot.send_message(chat_id=user[0], text=f'<b>✅  Ваш баланс изменён на {value}!</b>',
                           reply_markup=await kb.user_back_keyboard())
@heandlers.message(FSM.set_value_to_update_balance)
async def set_value_to_update_balance(message: Message, state: FSMContext, bot: Bot):
    value = message.text
    try:
        value = float(value)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Введите число',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_value_to_update_balance)
        return
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    username = data['username']
    if username[0] == '@':
        username = username[1:]
    user = await get_user_by_username(username) or await check_user_name(username)
    await set_balance(user_id=user[0], value=value)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text=f'Баланс пользователя @{username} установлен на {value}',
                                reply_markup=await kb.admin_back_keyboard())
    await bot.send_message(chat_id=user[0], text=f'<b>✅  Ваш баланс установлен: {value}!</b>',
                           reply_markup=await kb.user_back_keyboard())
@heandlers.message(FSM.set_shablon_count)
async def set_shablon_count(message: Message, state: FSMContext, bot: Bot):
    try:
        count = int(message.text)
    except ValueError:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        data = await state.get_data()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='⚠  Введите число',
                                    reply_markup=await kb.admin_back_keyboard())
        await state.set_state(FSM.set_shablon_count)
        return
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    game = await get_game(data['game_id'])
    prize = await get_prize(prize_id=data['prize_id'])
    await add_prize(count=count, prize_text=prize[1], game_id=data['game_id'])
    prizes = await get_prizes(game[0])
    await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'],
                               text=f'Шаблон успешно добавлен',
                                reply_markup=await kb.admin_prizes_keyboard(prizes, game[0]))
    await state.clear()
@heandlers.message(Command(commands=['talkers']))
async def show_talkers(message: Message, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if True:
        today = await get_today_messages()
        week = await get_week_messages()
        month = await get_month_messages()
        count_today = 0
        count_this_week = 0
        count_this_month = 0
        text = '<b>Статистика активности пользователей:</b>\n\n'
        for msg in today:
            count_today += msg[3]
        for msg in week:
            count_this_week += msg[3]
        for msg in month:
            count_this_month += msg[3]
        if today:
            user1, user2, user3 = None, None, None
            text += (f'<b>Статистика за сегодня:</b>\n'
                f'<i>Сообщений: {count_today}\n</i>')
            if len(today) >= 1:
                user1 = await get_user(user_id=today[0][0])
                if len(today) >= 2:
                    user2 = await get_user(user_id=today[1][0])
                    if len(today) >= 3:
                        user3 = await get_user(user_id=today[2][0])
            if user1:
                text += f'<b>🥇  Победтель:\n'
                if user1[12] == 0:
                    text += f'✨  @{user1[1]}: {today[0][3]} cообщений\n</b>'
                else:
                    text += f'🕶  Анонимный пользователь: {today[0][3]} cообщений\n</b>'
                if user2:
                    text += f'<b>🥈  Второе место:\n'
                    if user2[12] == 0:
                        text += f'✨  @{user2[1]}: {today[1][3]} cообщений\n</b>'
                    else:
                        text += f'🕶  Анонимный пользователь: {today[1][3]} cообщений\n</b>'
                    if user3:
                        text += f'<b>🥉  Третье место:\n'
                        if user3[12] == 0:
                            text += f'✨  @{user3[1]}: {today[2][3]} cообщений\n</b>'
                        else:
                            text += f'🕶  Анонимный пользователь: {today[2][3]} cообщений\n</b>'
        text += f'\n'
        user1 = None
        user2 = None
        user3 = None
        if week:
            text += f'<b>Статистика за неделю:</b>\n<i>Сообщений: {count_this_week}\n</i>'
            if len(week) >= 1:
                user1 = await get_user(user_id=week[0][0])
                if len(week) >= 2:
                    user2 = await get_user(user_id=week[1][0])
                    if len(week) >= 3:
                        user3 = await get_user(user_id=week[2][0])
            if user1:
                text += f'<b>🥇  Победтель:\n'
                if user1[12] == 0:
                    text += f'✨  @{user1[1]}: {week[0][3]} cообщений\n</b>'
                else:
                    text += f'🕶  Анонимный пользователь: {week[0][3]} cообщений\n</b>'
                if user2:
                    text += f'<b>🥈  Второе место:\n'
                    if user2[12] == 0:
                        text += f'✨  @{user2[1]}: {week[1][3]} cообщений\n</b>'
                    else:
                        text += f'🕶  Анонимный пользователь: {week[1][3]} cообщений\n</b>'
                    if user3:
                        text += f'<b>🥉  Третье место:\n'
                        if user3[12] == 0:
                            text += f'✨  @{user3[1]}: {week[2][3]} cообщений\n</b>'
                        else:
                            text += f'🕶  Анонимный пользователь: {week[2][3]} cообщений\n</b>'
        text += f'\n'
        user1 = None
        user2 = None
        user3 = None
        if month:
            text += f'<b>Статистика за месяц:</b>\n<i>Сообщений: {count_this_month}\n</i>'
            if month:
                user1 = await get_user(user_id=month[0][0])
                if len(month) >= 2:
                    user2 = await get_user(user_id=month[1][0])
                    if len(month) >= 3:
                        user3 = await get_user(user_id=month[2][0])
            if user1:
                text += f'<b>🥇  Победтель:\n'
                if user1[12] == 0:
                    text += f'✨  @{user1[1]}: {month[0][3]} cообщений\n</b>'
                else:
                    text += f'🕶  Анонимный пользователь: {month[0][3]} cообщений\n</b>'
                if user2:
                    text += f'<b>🥈  Второе место:\n'
                    if user2[12] == 0:
                        text += f'✨  @{user2[1]}: {month[1][3]} cообщений\n</b>'
                    else:
                        text += f'🕶  Анонимный пользователь: {month[1][3]} cообщений\n</b>'
                    if user3:
                        text += f'<b>🥉  Третье место:\n'
                        if user3[12] == 0:
                            text += f'✨  @{user3[1]}: {month[2][3]} cообщений\n</b>'
                        else:
                            text += f'🕶  Анонимный пользователь: {month[2][3]} cообщений\n</b>'
        await message.answer(text=text)
@heandlers.message(Command(commands=['ban']))
async def ban_user(message: Message, bot: Bot, command: CommandObject):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    if await is_admin(message=message):
        reply = message.reply_to_message
        if reply:
            username = reply.from_user.username
            user_id = reply.from_user.id
            until_date = await ban_parse_time(command.args, bot, message)
            if until_date:
                with suppress(TelegramBadRequest):
                    await bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id, until_date=until_date)
                    await ban_user_db(user_id=user_id, time=until_date)
                    await bot.send_message(chat_id=message.chat.id, text=f'<i>⛔  Пользователь заблокирован @{username} '
                                           f' до {until_date}</b>')
                    return
            else:
                return
        else:
            await bot.send_message(chat_id=message.from_user.id, text='<i>ℹ️  Для блоировки пользователя ответьте на '
                                   'его сообщение командой /ban и укажите время блокировки: m - минуты, h - часы, '
                                   'd - дни, w - недели (например: /ban 1h, /ban 2d, /ban 15m)</i>',
                                   reply_markup=await kb.admin_keyboard())
            return
    else:
        await bot.send_message(chat_id=message.from_user.id, text='<i>ℹ️  Заблокировать пользователя может только '
                                                                  'администратор</i>',
                               reply_markup=await kb.user_back_keyboard())
        return
@heandlers.message(Command(commands=['unban']))
async def unban_user(message: Message, bot: Bot):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    if await is_admin(message=message):
        reply = message.reply_to_message
        if reply:
            username = reply.from_user.username
            user_id = reply.from_user.id
            with suppress(TelegramBadRequest):
                await bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id)
                await unban_user_db(user_id=user_id)
                await bot.send_message(chat_id=message.chat.id,
                                       text=f'<b>✅  Пользователь разблокирован @{username}</b>')
                return
        else:
            await bot.send_message(chat_id=message.from_user.id, text='<i>ℹ️  Для разблоировки пользователя ответьте на'
                                   ' его сообщение командой /unban</i>', reply_markup=await kb.admin_keyboard())
            return
    else:
        await bot.send_message(chat_id=message.from_user.id, text='<i>ℹ️  Разблокировать пользователя может только '
                                                                  'администратор</i>',
                               reply_markup=await kb.user_back_keyboard())
        return
@heandlers.message(Command(commands=['mute']))
async def mute_user(message: Message, bot: Bot, command: CommandObject):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    if await is_admin(message=message):
        reply = message.reply_to_message
        if reply:
            username = reply.from_user.username
            user_id = reply.from_user.id
            until_date = await mute_parse_time(command.args, bot, message)
            if until_date:
                with suppress(TelegramBadRequest):
                    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, until_date=until_date,
                                                   permissions=ChatPermissions(can_send_messages=False,
                                                   can_send_audios=False, can_send_documents=False,
                                                   can_send_photos=False, can_send_videos=False, can_send_polls=False,
                                                   can_send_video_notes=False, can_send_voice_notes=False))
                    await bot.send_message(chat_id=message.chat.id, text=f'<b>🔇  Пользователя @{username} заткнули'
                                           f' до {until_date.strftime("%d.%m.%Y %H:%M")}</b>')
                    return
            else:
                return
        else:
            await bot.send_message(chat_id=message.from_user.id, text='<i>ℹ️  Для мута пользователя ответьте на его '
                                   'сообщение командой /mute и укажите время мута: m - минуты, h - часы, '
                                   'd - дни, w - недели (например: /mute 1h, /mute 2d, /mute 15m)</i>',
                                   reply_markup=await kb.admin_keyboard())
            return
    else:
        await bot.send_message(chat_id=message.from_user.id, text='<i>ℹ️  Замутить пользователя может только '
                                                                  'администратор</i>',
                               reply_markup=await kb.user_back_keyboard())
        return
@heandlers.message(Command(commands=['unmute']))
async def unmute_user(message: Message, bot: Bot):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    if await is_admin(message=message):
        reply = message.reply_to_message
        if reply:
            username = reply.from_user.username
            user_id = reply.from_user.id
            with suppress(TelegramBadRequest):
                await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, permissions=CHAT_PERMISSIONS)
                await bot.send_message(chat_id=message.chat.id, text=f'<b>✅  Пользователь @{username} размучен</b>')
                return
        else:
            await bot.send_message(chat_id=message.from_user.id, text='ℹ️  <i>Для размута пользователя ответьте на '
                                   'его сообщение командой /unmute</i>', reply_markup=await kb.admin_keyboard())
            return
    else:
        await bot.send_message(chat_id=message.from_user.id, text='ℹ️  <i>Размутить пользователя может только '
                                                                  'администратор</i>',
                               reply_markup=await kb.user_back_keyboard())
        return
@heandlers.message(Command(commands=['+karma']))
async def add_karma(message: Message, bot: Bot):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    reply = message.reply_to_message
    if reply:
        if reply.from_user.id == message.from_user.id:
            await bot.send_message(chat_id=message.from_user.id, text='ℹ️  <i>Вы не можете увеличить свою карму</i>')
            return
        username = reply.from_user.username
        user_id = reply.from_user.id
        if await add_karma_db(user_id=message.from_user.id, target_id=user_id):
            await bot.send_message(chat_id=message.chat.id, text=f'🔝  <b>Карма пользователя @{username} увеличена на '
                                  f'1 ед. пользователем @{message.from_user.username}</b>')
        else:
            await bot.send_message(chat_id=message.chat.id, text=f'⚠  <b>Подождите {KARMA_TIMEOUT} минут</b>')
        return
    else:
        await bot.send_message(chat_id=message.from_user.id, text='ℹ️  <i>Для увеличения кармы пользователя ответьте на'
                               ' его сообщение командой /+karma</i>')
        return
@heandlers.message(Command(commands=['all']))
async def all_call(message: Message, bot: Bot, command: CommandObject):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    usernames = await get_usernames()
    smiles = ['🍇', '🍉', '🍓', '🍒', '🎈', '🎨', '🎃', '👒', '🎮', '🌎', '🍕', '🧊', '🍦', '🌈', '☂', '🔥', '❄',
              '🛴', '🚘', '🚗', '🚦', '🌃', '🛹', '⚽', '💎', '🎯', '🍺', '🌵', '🌿', '🥕', '🥑', '🍍', '🍆', '🥥',
              '🥭', '🍏', '🍄', '🌭', '😎', '😴', '😊', '😋', '😀', '😥', '😫', '😈', '🐢', '👅', '👠']
    text, random_smiles = '', ''
    for username in usernames:
        random_smiles += f'<a href="tg://resolve?domain={username[0]}">{(random.choice(smiles))}</a>'
        if username[0] != message.from_user.username:
            text += f'@{username[0]}\n'
    if command:
        text += command.args
    if text:
        msg = await bot.send_message(chat_id=message.chat.id, text=text)
        await asyncio.sleep(0.1)
        await bot.edit_message_text(text=f'Призыв от '        
        f'{"@"+message.from_user.username if message.from_user.username else message.from_user.first_name} '
                                         f'\n{random_smiles}\n' + command.args, message_id=msg.message_id,
                                    chat_id=message.chat.id)
@heandlers.message(Command(commands=['mykarma']))
async def mykarma(message: Message, bot: Bot):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    user = await get_user(user_id=message.from_user.id)
    await bot.send_message(chat_id=message.chat.id, text=f'✨  Ваша карма: {user[4]}')
@heandlers.message(Command(commands=['history']))
async def show_history(message: Message, bot: Bot):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    games = await get_game_history()
    text = ''
    if games:
        text += f'<b>Всего проведено игр: <i>{len(games)}</i></b>'
        for game in games:
            users_count = await get_game_users_count(game_id=game[0])
            prize_count = await get_game_winners_count(game_id=game[0])
            text += (f'<b>Игра {game[1]}\nКоличество игроков: {users_count}\nКоличество победителей: {prize_count}\n'
                     f'Дата начала: {game[5]}\nДата окончания: {game[6]}\n</b>')
            winners = await get_game_winners(game_id=game[0])
            if winners:
                for winner in winners:
                    user = await get_user(winner[0])
                    prize = await get_prize(prize_id=winner[1])
                    text += f'<i>@{user[1]} - {prize[1]}</i>\n'
            else:
                text += 'Победителей нет\n'
            text += '\n'
    else:
        text = 'История игр пуста'
    await message.answer(text=text)
@heandlers.message(Command(commands=['winners']))
async def show_winners(message: Message, bot: Bot):
    if message.chat.type == 'private':
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        return
    winners = await get_all_winners()
    text = ''
    count, check = 0, 0
    for winner in winners:
        count += 1
        if count == 1:
            text += f'<b>🥇  Победитель:</b>\n'
        elif count == 2:
            text += f'<b>🥈  Второе место:</b>\n'
        elif count == 3:
            text += f'<b>🥉  Третье место:</b>\n'
        else:
            break
        user = await get_user(winner[0])
        balance = 0
        przs = await get_winner_prizes(user_id=winner[0])
        if user[12] == 0:
            text += f'✨  @{user[1]}:\n'
        else:
            text += f'🕶  Анонимный пользователь:\n'
        text += f'<b>📃  Всего побед: {winner[1]}</b>\n'
        for prz in przs:
            prize = await get_prize(prize_id=prz[1])
            match_ = re.match(r"(\d+)", prize[1].lower())
            try:
                if match_:
                    value = match_.group(1)
                    value = int(value)
                    balance += value
                else:
                    check += 1
                    if check == 1:
                        text += f'<b>🎁  Дополнительные призы:</b>\n'
                    text += f'🎉  <i>{prize[1]}</i>\n'
            except ValueError:
                check += 1
                if check == 1:
                    text += f'<b>🎁  Дополнительные призы:</b>\n'
                text += f'✨  <i>{prize[1]}</i>\n'
        if balance:
            text += f'💰  <b><i>Выиграно: {balance}</i></b>\n'
        text += '\n'
    games_month = await get_games_month()
    games_all = await get_game_history()
    text += f'<b>📅  Игр проведено за месяц: {len(games_month)}\n📅  Игр проведено всего: {len(games_all)}</b>\n'
    prizes_month = await get_prizes_month()
    prizes_all = await get_prizes_all()
    month_payed = 0
    all_payed = 0
    for prize in prizes_month:
        match_ = re.match(r"(\d+)", prize[1].lower())
        try:
            if match_:
                value = match_.group(1)
                value = int(value)
                month_payed += value
            else:
                pass
        except ValueError:
            pass
    for prize in prizes_all:
        match_ = re.match(r"(\d+)", prize[1].lower())
        try:
            if match_:
                value = match_.group(1)
                value = int(value)
                all_payed += value
            else:
                pass
        except ValueError:
            pass
    text += f'<b>💵  Выплачено за месяц: {month_payed}\n💵  Выплачено всего: {all_payed}</b>'
    if text:
        await message.answer(text=text)
    else:
        await message.answer(text='Победителей нет')
@heandlers.message(FSM.set_new_prize_text)
async def set_new_prize_text(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    data = await state.get_data()
    message_id = data['message_id']
    prize_id = data['prize_id']
    await prize_update_text(prize_id, text)
    game = await get_last_game()
    prizes = await get_prizes(game_id=game[0])
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id, text=f'Текст приза изменён на {text}',
                                reply_markup=await kb.admin_prizes_keyboard(prizes, game[0]))
    await state.clear()
@heandlers.message(FSM.set_prize_text)
async def set_prize_text(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    data = await state.get_data()
    message_id = data['message_id']
    await state.update_data(text=text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id, message_id=message_id, text=f'Теперь введите количество '
                                f'призов', reply_markup=await kb.admin_game_prize_keyboard())
    await state.set_state(FSM.set_prize_count)
@heandlers.message(FSM.set_prize_count)
async def set_prize_count(message: Message, state: FSMContext, bot: Bot):
    try:
        count = int(message.text)
        data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await add_prize(game_id=data['game_id'], prize_text=data['text'], count=count)
        prizes = await get_prizes(game_id=data['game_id'])
        prizes_count = 0
        for prize in prizes:
            prizes_count += prize[3]
        game = await get_last_game()
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text=f'Призовых мест указан'
                                    f'о в игре: {game[3]}\nКоличество добавленных призов: {prizes_count}\n'
                                    'Призы текущей игры:',
                                    reply_markup=await kb.admin_prizes_keyboard(prizes=prizes, game_id=data['game_id']))
        await state.clear()
    except ValueError:
        data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Необходимо написать '
                                    'число', reply_markup=await kb.admin_text_prize_keyboard(data['prize_id']))
        await state.set_state(FSM.set_prize_count)
@heandlers.message(FSM.set_new_prize_count)
async def set_new_prize_count(message: Message, state: FSMContext, bot: Bot):
    try:
        count = int(message.text)
        data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await prize_update_count(data['prize_id'], count)
        prize = await get_prize(prize_id=data['prize_id'])
        game = await get_last_game()
        prizes = await get_prizes(game_id=game[0])
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text=f'Количество призов '
                                   f'изменено на {count}',
                                    reply_markup=await kb.admin_prizes_keyboard(prizes, prize[2]))

        await state.clear()
    except ValueError:
        data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.edit_message_text(chat_id=message.chat.id, message_id=data['message_id'], text='Необходимо написать '
                                    'число', reply_markup=await kb.admin_text_prize_keyboard(data['prize_id']))
        await state.set_state(FSM.set_new_prize_count)
async def mute_parse_time(time: str, bot: Bot, message: Message) -> datetime:
    if time:
        match_ = re.match(r"(\d+)([а-я])", time.lower().strip())
        if match_:
            value = int(match_.group(1))
            time = match_.group(2)
            match time:
                case 'm':
                    return datetime.datetime.now() + datetime.timedelta(minutes=value)
                case 'h':
                    return datetime.datetime.now() + datetime.timedelta(hours=value)
                case 'd':
                    return datetime.datetime.now() + datetime.timedelta(days=value)
                case 'w':
                    return datetime.datetime.now() + datetime.timedelta(weeks=value)
                case _:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='ℹ️  Для мута пользователя ответьте на его '
                                           'сообщение командой /mute и укажите время блокировки: m - минуты, h - часы, '
                                           'd - дни, w - недели (например: /mute 1h, /mute 2d, /mute 15m, /ban 3w)',
                                           reply_markup=await kb.admin_keyboard())
                    return
        else:
            return
    else:
        await bot.send_message(chat_id=message.from_user.id, text='Для блоировки пользователя ответьте на его '
                               'сообщение командой /ban и укажите время блокировки: m - минуты, h - часы, d - дни, w - '
                               'недели (например: /ban 1h, /ban 2d, /ban 15m, /ban 3w)',
                               reply_markup=await kb.admin_keyboard())
        return
async def ban_parse_time(time: str, bot: Bot, message: Message) -> datetime:
    if time:
        match_ = re.match(r"(\d+)([а-я])", time.lower().strip())
        if match_:
            value = int(match_.group(1))
            time = match_.group(2)
            match time:
                case 'm':
                    return datetime.datetime.now() + datetime.timedelta(minutes=value)
                case 'h':
                    return datetime.datetime.now() + datetime.timedelta(hours=value)
                case 'd':
                    return datetime.datetime.now() + datetime.timedelta(days=value)
                case 'w':
                    return datetime.datetime.now() + datetime.timedelta(weeks=value)
                case _:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text='ℹ️  Для блоировки пользователя ответьте на его '
                                           'сообщение командой /ban и укажите время блокировки: m - минуты, h - часы, '
                                           'd - дни, w - недели (например: /ban 1h, /ban 2d, /ban 15m, /ban 3w)',
                                           reply_markup=await kb.admin_keyboard())
                    return
        else:
            return
    else:
        await bot.send_message(chat_id=message.from_user.id, text='Для блоировки пользователя ответьте на его '
                               'сообщение командой /ban и укажите время блокировки: m - минуты, h - часы, d - дни, w - '
                               'недели (например: /ban 1ч, /ban 2д, /ban 15м)', reply_markup=await kb.admin_keyboard())
        return
@heandlers.message()
async def catch_message(message: Message, bot: Bot):
    if message.chat.type == 'supergroup' or message.chat.type == 'channel' or message.chat.type == 'group':
        await add_message(message.from_user.id, message.from_user.username)
    else:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
