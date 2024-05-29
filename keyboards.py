import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from cfg import ADMIN_ACCOUNT_URL, BOT_USERNAME
from db import get_active_game, get_address, get_prize, get_last_game, get_game_user, get_user, \
    check_weekly_user, check_monthly_user, check_daily_user, \
    get_daily_users_count, get_weekly_users_count, get_monthly_users_count, get_send, get_scheduled_send, \
    get_unread_messages_count_from_sender, get_message, get_unread_messages_count
async def admin_accept_message_keyboard():
    admin_accept_message_kb = InlineKeyboardBuilder()
    admin_accept_message_kb.add(InlineKeyboardButton(text='Подтвердить отправку', callback_data='admin_accept_message'))
    admin_accept_message_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_messages'))
    return admin_accept_message_kb.adjust(1).as_markup()

async def admin_messages_keyboard(unread_count):
    admin_messages_kb = InlineKeyboardBuilder()
    admin_messages_kb.add(InlineKeyboardButton(text=f'{"("+str(unread_count)+")" if unread_count > 0 else ""}Почта',
                                               callback_data='admin_messages_post'))
    admin_messages_kb.add(InlineKeyboardButton(text='Отправить сообщение', callback_data='admin_messages_send'))
    admin_messages_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_messages_kb.adjust(1).as_markup()
async def admin_messages_post_keyboard(messages, unread_messages, user_id):
    admin_messages_post_kb = InlineKeyboardBuilder()
    for message in messages:
        for user in unread_messages:
            if message[1] in user:
                count = await get_unread_messages_count_from_sender(user_id, message[1])
                sender = await get_user(message[1])
                admin_messages_post_kb.add(InlineKeyboardButton(text=
                                                            f'{"("+str(count)+")"}'
                                                            f'От {sender[1] if sender[1] else sender[2]}',
                                                            callback_data=f'admin_messages_from_{message[1]}'))
                break
        else:
            sender = await get_user(message[1])
            admin_messages_post_kb.add(InlineKeyboardButton(text=f'От {sender[1] if sender[1] else sender[2]}',
                                                            callback_data=f'admin_messages_from_{message[1]}'))
    admin_messages_post_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_messages'))
    return admin_messages_post_kb.adjust(1).as_markup()
async def admin_messages_from_keyboard(messages):
    admin_messages_from_kb = InlineKeyboardBuilder()
    for message in messages:
        admin_messages_from_kb.add(InlineKeyboardButton(text=f'{"* " if message[5] == 0 else ""}'+message[4],
                                                        callback_data=f'admin_message_{message[0]}'))
    admin_messages_from_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_messages_post'))
    return admin_messages_from_kb.adjust(1).as_markup()
async def admin_message_keyboard(message_id):
    admin_message_kb = InlineKeyboardBuilder()
    admin_message_kb.add(InlineKeyboardButton(text='Ответить пользователю',
                                            callback_data=f'admin_answer_message_{message_id}'))
    admin_message_kb.add(InlineKeyboardButton(text='Отметить как непрочитанное',
                                            callback_data=f'admin_unread_message_{message_id}'))
    admin_message_kb.add(InlineKeyboardButton(text='Удалить сообщение',
                                            callback_data=f'admin_delete_message_{message_id}'))
    message = await get_message(message_id)
    admin_message_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_messages_from_{message[2]}'))
    return admin_message_kb.adjust(1).as_markup()
async def admin_accept_delete_message_keyboard(message_id):
    admin_accept_delete_message_kb = InlineKeyboardBuilder()
    admin_accept_delete_message_kb.add(InlineKeyboardButton(text='Удалить сообщение',
                                                          callback_data=f'admin_accept_delete_message_{message_id}'))
    admin_accept_delete_message_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_message_{message_id}'))
    return admin_accept_delete_message_kb.adjust(1).as_markup()
async def admin_back_to_messages_keyboard():
    admin_back_to_messages_kb = InlineKeyboardBuilder()
    admin_back_to_messages_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_messages_post'))
    return admin_back_to_messages_kb.adjust(1).as_markup()
async def admin_accept_answer_keyboard(sender_id):
    admin_accept_answer_kb = InlineKeyboardBuilder()
    admin_accept_answer_kb.add(InlineKeyboardButton(text='Отправить', callback_data='admin_send_answer'))
    admin_accept_answer_kb.add(InlineKeyboardButton(text='Отмена', callback_data=f'admin_messages_from_{sender_id}'))
    return admin_accept_answer_kb.adjust(1).as_markup()
async def start_keyboard(buttons: list):
    start_kb = InlineKeyboardBuilder()
    if buttons:
        for button in buttons:
            start_kb.add(InlineKeyboardButton(text=button['button_text'], url=button['button_url']))
        start_kb.add(InlineKeyboardButton(text='🔍  Проверить подписку', callback_data='check_subscribe'))
        return start_kb.adjust(1).as_markup()
    return user_back_keyboard()
async def join_keyboard(buttons: list):
    start_kb = InlineKeyboardBuilder()
    if buttons:
        for button in buttons:
            start_kb.add(InlineKeyboardButton(text=button['button_text'], url=button['button_url']))
        start_kb.add(InlineKeyboardButton(text='🔍  Проверить подписку', callback_data='check_join_subscribe'))
        return start_kb.adjust(1).as_markup()
    return await user_back_keyboard()
async def admin_url_keyboard(status: bool = True):
    admin_url_kb = InlineKeyboardBuilder()
    admin_url_kb.add(InlineKeyboardButton(text='📲  Написать администратору', url=ADMIN_ACCOUNT_URL))
    if status:
        admin_url_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_menu'))
    return admin_url_kb.adjust(1).as_markup()
async def admin_keyboard(active: int = 2, messages_count: int = 0):
    game = await get_last_game()
    admin_kb = InlineKeyboardBuilder()
    admin_kb.add(InlineKeyboardButton(text='Создать новую игру', callback_data='admin_new_game'))
    if active == 1:
        admin_kb.add(InlineKeyboardButton(text='Текущая игра (активна)', callback_data='admin_current_game'))
        admin_kb.add(InlineKeyboardButton(text='Призы текущей игры', callback_data=f'admin_game_prizes_{game[0]}'))
    elif active == 0:
        admin_kb.add(InlineKeyboardButton(text='Текущая игра (неактивна)', callback_data='admin_current_game'))
        admin_kb.add(InlineKeyboardButton(text='Призы текущей игры', callback_data=f'admin_game_prizes_{game[0]}'))
    admin_kb.add(InlineKeyboardButton(text='Доступные промокоды', callback_data='admin_addresses'))
    admin_kb.add(InlineKeyboardButton(text='История игр', callback_data='admin_game_history'))
    admin_kb.add(InlineKeyboardButton(text='Настройка лотереи', callback_data='admin_loto_settings'))
    admin_kb.add(InlineKeyboardButton(text='Статистика лотереи', callback_data='admin_loto'))
    admin_kb.add(InlineKeyboardButton(text='Продлить подписку VIP', callback_data='admin_vip_subscribe'))
    admin_kb.add(InlineKeyboardButton(text='Продлить подписку на бота', callback_data='admin_bot_subscribe'))
    admin_kb.add(InlineKeyboardButton(text='Обновление баланса пользователя', callback_data='admin_edit_balance'))
    admin_kb.add(InlineKeyboardButton(text='Рассылка обявлений', callback_data='admin_sends'))
    admin_kb.add(InlineKeyboardButton(text=f'{"("+str(messages_count)+")" if messages_count > 0 else ""}'
                                      f'Отправить сообщение через бота',
                                      callback_data='admin_messages'))
    admin_kb.add(InlineKeyboardButton(text='Меню модераторов', callback_data='admin_moderators'))
    admin_kb.add(InlineKeyboardButton(text='Настройки бота', callback_data='admin_settings'))
    admin_kb.add(InlineKeyboardButton(text='Донаты', callback_data='admin_donates'))
    return admin_kb.adjust(1).as_markup()
async def moderator_keyboard(active: int = 2):
    game = await get_last_game()
    admin_kb = InlineKeyboardBuilder()
    admin_kb.add(InlineKeyboardButton(text='Создать новую игру', callback_data='admin_new_game'))
    if active == 1:
        admin_kb.add(InlineKeyboardButton(text='Текущая игра (активна)', callback_data='admin_current_game'))
        admin_kb.add(InlineKeyboardButton(text='Призы текущей игры', callback_data=f'admin_game_prizes_{game[0]}'))
    elif active == 0:
        admin_kb.add(InlineKeyboardButton(text='Текущая игра (неактивна)', callback_data='admin_current_game'))
        admin_kb.add(InlineKeyboardButton(text='Призы текущей игры', callback_data=f'admin_game_prizes_{game[0]}'))
    admin_kb.add(InlineKeyboardButton(text='Доступные промокоды', callback_data='admin_addresses'))
    admin_kb.add(InlineKeyboardButton(text='История игр', callback_data='admin_game_history'))
    admin_kb.add(InlineKeyboardButton(text='Настройка лотереи', callback_data='admin_loto_settings'))
    admin_kb.add(InlineKeyboardButton(text='Статистика лотереи', callback_data='admin_loto'))
    admin_kb.add(InlineKeyboardButton(text='Продлить подписку VIP', callback_data='admin_vip_subscribe'))
    admin_kb.add(InlineKeyboardButton(text='Продлить подписку на бота', callback_data='admin_bot_subscribe'))
    admin_kb.add(InlineKeyboardButton(text='Обновление баланса пользователя', callback_data='admin_edit_balance'))
    admin_kb.add(InlineKeyboardButton(text='Рассылка обявлений', callback_data='admin_sends'))
    admin_kb.add(InlineKeyboardButton(text='Меню модераторов', callback_data='admin_moderators'))
    admin_kb.add(InlineKeyboardButton(text='Настройки бота', callback_data='admin_settings'))
    admin_kb.add(InlineKeyboardButton(text='Донаты', callback_data='admin_donates'))
    return admin_kb.adjust(1).as_markup()
async def admin_settings_keyboard():
    admin_settings_kb = InlineKeyboardBuilder()
    admin_settings_kb.add(InlineKeyboardButton(text='Защита от спама', callback_data='admin_antispam'))
    admin_settings_kb.add(InlineKeyboardButton(text='Принятие заявок', callback_data='admin_request'))
    admin_settings_kb.add(InlineKeyboardButton(text='Прощальное сообщение', callback_data='admin_goodbye'))
    admin_settings_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_settings_kb.adjust(1).as_markup()
async def admin_goodbye_keyboard(value):
    admin_goodbye_kb = InlineKeyboardBuilder()
    if value == 0:
        admin_goodbye_kb.add(InlineKeyboardButton(text='Включить прощальное сообщение',
                                                  callback_data='admin_goodbye_on'))
    else:
        admin_goodbye_kb.add(InlineKeyboardButton(text='Отключить прощальное сообщение',
                                                  callback_data='admin_goodbye_off'))
    admin_goodbye_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_settings'))
    return admin_goodbye_kb.adjust(1).as_markup()
async def leave_chat_keyboard(link):
    leave_chat_kb = InlineKeyboardBuilder()
    leave_chat_kb.add(InlineKeyboardButton(text='✅  Вернуться в чат!', url=link))
    return leave_chat_kb.adjust(1).as_markup()
async def admin_request_keyboard(value):
    admin_request_kb = InlineKeyboardBuilder()
    if value == 0:
        admin_request_kb.add(InlineKeyboardButton(text='Включить принятие заявок', callback_data='admin_request_on'))
    else:
        admin_request_kb.add(InlineKeyboardButton(text='Отключить принятие заявок', callback_data='admin_request_off'))
    admin_request_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_settings'))
    return admin_request_kb.adjust(1).as_markup()
async def admin_antispam_keyboard(antispam):
    admin_antispam_kb = InlineKeyboardBuilder()
    admin_antispam_kb.add(InlineKeyboardButton(text='Изменить значение блокировки', callback_data='admin_antispam_edit'))
    if antispam == 0:
        admin_antispam_kb.add(InlineKeyboardButton(text='Включить антиспам', callback_data='admin_antispam_on'))
    else:
        admin_antispam_kb.add(InlineKeyboardButton(text='Отключить антиспам', callback_data='admin_antispam_off'))
    admin_antispam_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_settings'))
    return admin_antispam_kb.adjust(1).as_markup()
async def admin_back_to_antispam_keyboard():
    admin_back_to_antispam_kb = InlineKeyboardBuilder()
    admin_back_to_antispam_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_antispam'))
    return admin_back_to_antispam_kb.adjust(1).as_markup()
async def admin_later_keyboard(scheds, page: int = 0):
    admin_later_kb = InlineKeyboardBuilder()
    len_ = len(scheds)
    scheds = scheds[page*45:page*45+45]
    for sched in scheds:
        send = await get_send(sched[0])
        admin_later_kb.row(InlineKeyboardButton(text=f'{"(Активная) " if sched[6] == 1 else ""}'
                                                     f'{sched[1]}: {send[1] if send[1] else "Медиа"}',
                                                callback_data=f'admin_laterr_{sched[4]}'))
    if page > 0 and len_ > (page + 1) * 45:
        admin_later_kb.row(InlineKeyboardButton(text='Назад', callback_data=f'admin_later_{page-1}'),
                           InlineKeyboardButton(text='Вперед', callback_data=f'admin_later_{page+1}'))
    elif len_ > (page + 1) * 45:
        admin_later_kb.row(InlineKeyboardButton(text='Вперед', callback_data=f'admin_later_{page+1}'))
    elif page > 0:
        admin_later_kb.row(InlineKeyboardButton(text='Назад', callback_data=f'admin_later_{page-1}'))
    admin_later_kb.row(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_later_kb.as_markup()
async def admin_scheduled_keyboard(send_id, status: bool = False):
    admin_scheduled_kb = InlineKeyboardBuilder()
    sched = await get_scheduled_send(send_id)
    if sched[-1] == 1:
        admin_scheduled_kb.add(InlineKeyboardButton(text='Отменить рассылку',
                                                    callback_data=f'admin_deactivate_scheduled_{send_id}'))
    else:
        admin_scheduled_kb.add(InlineKeyboardButton(text='Запустить рассылку',
                                                    callback_data=f'admin_activate_scheduled_{send_id}'))
    admin_scheduled_kb.add(InlineKeyboardButton(text='Удалить рассылку',
                                                callback_data=f'admin_delete_scheduled_{send_id}'))
    if status:
        admin_scheduled_kb.add(InlineKeyboardButton(text='Изменить время начала рассылки',
                                                    callback_data=f'admin_timestart_scheduled_{send_id}'))
        admin_scheduled_kb.add(InlineKeyboardButton(text='Изменить время окончания рассылки',
                                                    callback_data=f'admin_timeend_scheduled_{send_id}'))
    admin_scheduled_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends'))
    return admin_scheduled_kb.adjust(1).as_markup()
async def admin_back_to_later_keyboard():
    admin_back_to_later_kb = InlineKeyboardBuilder()
    admin_back_to_later_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_later_0'))
    return admin_back_to_later_kb.adjust(1).as_markup()
async def admin_back_to_interval_keyboard():
    admin_back_to_interval_kb = InlineKeyboardBuilder()
    admin_back_to_interval_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_intervals_0'))
    return admin_back_to_interval_kb.adjust(1).as_markup()
async def admin_interval_keyboard(scheds, page: int = 0):
    admin_interval_kb = InlineKeyboardBuilder()
    len_ = len(scheds)
    scheds = scheds[page*45:page*45+45]
    for sched in scheds:
        send = await get_send(sched[0])
        admin_interval_kb.row(InlineKeyboardButton(text=f'{"("+sched[3]+") " if sched[6] == 1 else ""}'
                                                        f'{sched[1]}: {send[1] if send[1] else "Медиа"}',
                                                   callback_data=f'admin_intervall_{sched[4]}'))
    if page > 0 and len_ > (page + 1) * 45:
        admin_interval_kb.row(InlineKeyboardButton(text='Назад', callback_data=f'admin_intervals_{page-1}'),
                              InlineKeyboardButton(text='Вперед', callback_data=f'admin_intervals_{page+1}'))
    elif len_ > (page + 1) * 45:
        admin_interval_kb.row(InlineKeyboardButton(text='Вперед', callback_data=f'admin_intervals_{page+1}'))
    elif page > 0:
        admin_interval_kb.row(InlineKeyboardButton(text='Назад', callback_data=f'admin_intervals_{page-1}'))
    admin_interval_kb.row(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_interval_kb.as_markup()
async def admin_sends_chats_keyboard(sends, page: int = 0):
    admin_sends_chats_kb = InlineKeyboardBuilder()
    len_ = len(sends)
    sends = sends[page*45:page*45+45]
    for send in sends:
        admin_sends_chats_kb.row(InlineKeyboardButton(text=f'{send[1] if send[1] else "Медиа"}',
                                                    callback_data=f'admin_send_chat_{send[0]}'))
    if page > 0 and len_ > (page + 1) * 45:
        admin_sends_chats_kb.row(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_{page-1}'),
                              InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_{page+1}'))
    elif len_ > (page + 1) * 45:
        admin_sends_chats_kb.row(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_{page+1}'))
    elif page > 0:
        admin_sends_chats_kb.row(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_{page-1}'))
    admin_sends_chats_kb.row(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_sends_chats_kb.as_markup()
async def admin_chat_keyboard(chat_id):
    admin_chat_kb = InlineKeyboardBuilder()
    admin_chat_kb.add(InlineKeyboardButton(text='Удалить чат', callback_data=f'admin_delete_chat_{chat_id}'))
    admin_chat_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_chats'))
    return admin_chat_kb.adjust(1).as_markup()
async def admin_accept_delete_chat_keyboard(chat_id):
    admin_accept_delete_chat_kb = InlineKeyboardBuilder()
    admin_accept_delete_chat_kb.add(InlineKeyboardButton(text='Подтвердить удаление',
                                                         callback_data=f'admin_accept_delete_chat_{chat_id}'))
    admin_accept_delete_chat_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_chat_{chat_id}'))
    return admin_accept_delete_chat_kb.adjust(1).as_markup()
async def admin_sends_keyboard():
    admin_sends_kb = InlineKeyboardBuilder()
    admin_sends_kb.add(InlineKeyboardButton(text='База данных сообщений', callback_data='admin_sends_database_0'))
    admin_sends_kb.add(InlineKeyboardButton(text='Запланированные сообщения', callback_data='admin_later_0'))
    admin_sends_kb.add(InlineKeyboardButton(text='Сообщения с интервалом', callback_data='admin_intervals_0'))
    admin_sends_kb.add(InlineKeyboardButton(text='Рассылка всем пользователям', callback_data='admin_sends_all_0'))
    admin_sends_kb.add(InlineKeyboardButton(text='Рассылка пользователям с VIP подпиской',
                                            callback_data='admin_sends_vip_0'))
    admin_sends_kb.add(InlineKeyboardButton(text='Рассылка пользователям без VIP подписки',
                                            callback_data='admin_sends_novip_0'))
    admin_sends_kb.add(InlineKeyboardButton(text='Рассылка сообшений в группы', callback_data='admin_sends_chats_0'))
    admin_sends_kb.add(InlineKeyboardButton(text='Группы', callback_data='admin_chats'))
    admin_sends_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_sends_kb.adjust(1).as_markup()
async def admin_chats_keyboard(chats):
    admin_chats_kb = InlineKeyboardBuilder()
    for chat in chats:
        admin_chats_kb.add(InlineKeyboardButton(text=f'{chat[1]}', callback_data=f'admin_chat_{chat[0]}'))
    admin_chats_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_chats_kb.adjust(1).as_markup()
async def admin_back_to_chats_keyboard():
    admin_back_to_chats_kb = InlineKeyboardBuilder()
    admin_back_to_chats_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_chats'))
    return admin_back_to_chats_kb.adjust(1).as_markup()
async def admin_sends_database_keyboard(sends, page: int = 0):
    admin_sends_database_kb = InlineKeyboardBuilder()
    len_ = len(sends)
    sends = sends[page*45:(page+1)*45]
    if sends:
        for send in sends:
            admin_sends_database_kb.add(InlineKeyboardButton(text=f'{send[1] if send[1] else "Медиа"}',
                                                             callback_data=f'admin_send_{send[0]}'))
    if page > 0 and len_ > (page + 1) * 45:
        admin_sends_database_kb.row(InlineKeyboardButton(text='Назад',
                                                         callback_data=f'admin_sends_database_{page-1}'),
                                    InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_database_{page+1}'))
    elif len_ > (page + 1) * 45:
        admin_sends_database_kb.row(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_database_{page+1}'))
    elif page > 0:
        admin_sends_database_kb.row(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_database_{page-1}'))
    admin_sends_database_kb.add(InlineKeyboardButton(text='Добавить сообщение', callback_data='admin_add_send'))
    admin_sends_database_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_sends_database_kb.adjust(1).as_markup()
async def admin_send_keyboard(send_id, buttons):
    admin_send_kb = InlineKeyboardBuilder()
    send = await get_send(send_id)
    for button in buttons:
        admin_send_kb.add(InlineKeyboardButton(text=button[2], callback_data=f'admin_button_{button[0]}'))
    admin_send_kb.add(InlineKeyboardButton(text='Изменить текст', callback_data=f'admin_text_send_{send_id}'))
    if send[2]:
        admin_send_kb.add(InlineKeyboardButton(text='Изменить медиа', callback_data=f'admin_media_send_{send_id}'))
        admin_send_kb.add(InlineKeyboardButton(text='Удалить медиа',
                                               callback_data=f'admin_delete_media_send_{send_id}'))
    else:
        admin_send_kb.add(InlineKeyboardButton(text='Добавить медиа', callback_data=f'admin_add_media_send_{send_id}'))
    admin_send_kb.add(InlineKeyboardButton(text='Добавить кнопку', callback_data=f'admin_add_button_{send_id}'))
    admin_send_kb.add(InlineKeyboardButton(text='Удалить', callback_data=f'admin_delete_send_{send_id}'))
    admin_send_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_database_0'))
    return admin_send_kb.adjust(1).as_markup()
async def admin_button_keyboard(button):
    admin_button_kb = InlineKeyboardBuilder()
    admin_button_kb.add(InlineKeyboardButton(text=f'{button[2]}', url=f'{button[3]}'))
    admin_button_kb.add(InlineKeyboardButton(text='Изменить ссылку', callback_data=f'admin_url_button_{button[0]}'))
    admin_button_kb.add(InlineKeyboardButton(text='Изменить текст', callback_data=f'admin_text_button_{button[0]}'))
    admin_button_kb.add(InlineKeyboardButton(text='Удалить кнопку', callback_data=f'admin_delete_button_{button[0]}'))
    admin_button_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_send_{button[1]}'))
    return admin_button_kb.adjust(1).as_markup()
async def admin_accept_delete_button_keyboard(button_id):
    admin_accept_delete_button_kb = InlineKeyboardBuilder()
    admin_accept_delete_button_kb.add(InlineKeyboardButton(text='Удалить кнопку',
                                                           callback_data=f'admin_accept_delete_button_{button_id}'))
    admin_accept_delete_button_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_button_{button_id}'))
    return admin_accept_delete_button_kb.adjust(1).as_markup()
async def admin_back_to_send_keyboard(send_id):
    admin_back_to_send_kb = InlineKeyboardBuilder()
    admin_back_to_send_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_send_{send_id}'))
    return admin_back_to_send_kb.adjust(1).as_markup()
async def admin_back_to_button_keyboard(button_id):
    admin_back_to_button_kb = InlineKeyboardBuilder()
    admin_back_to_button_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_button_{button_id}'))
    return admin_back_to_button_kb.adjust(1).as_markup()
async def admin_accept_delete_send_keyboard(send_id):
    admin_accept_delete_send_kb = InlineKeyboardBuilder()
    admin_accept_delete_send_kb.add(InlineKeyboardButton(text='Удалить сообщение',
                                                         callback_data=f'admin_accept_delete_send_{send_id}'))
    admin_accept_delete_send_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_send_{send_id}'))
    return admin_accept_delete_send_kb.adjust(1).as_markup()
async def admin_accept_delete_media_send_keyboard(send_id):
    admin_accept_delete_media_send_kb = InlineKeyboardBuilder()
    admin_accept_delete_media_send_kb.add(InlineKeyboardButton(text='Удалить медиа',
                                                              callback_data=f'admin_accept_delete_media_send_{send_id}'))
    admin_accept_delete_media_send_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_send_{send_id}'))
    return admin_accept_delete_media_send_kb.adjust(1).as_markup()
async def admin_send_text_keyboard():
    admin_send_text_kb = InlineKeyboardBuilder()
    admin_send_text_kb.add(InlineKeyboardButton(text='Продолжить без текста', callback_data='admin_add_send_no_text'))
    admin_send_text_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_send_text_kb.adjust(1).as_markup()
async def admin_send_media_keyboard():
    admin_send_media_kb = InlineKeyboardBuilder()
    admin_send_media_kb.add(InlineKeyboardButton(text='Продолжить без медиа', callback_data='admin_add_send_no_media'))
    admin_send_media_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_send_media_kb.adjust(1).as_markup()
async def admin_back_to_sends_keyboard():
    admin_back_to_sends_kb = InlineKeyboardBuilder()
    admin_back_to_sends_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_back_to_sends_kb.adjust(1).as_markup()
async def user_send_keyboard(buttons):
    user_send_kb = InlineKeyboardBuilder()
    for button in buttons:
        user_send_kb.add(InlineKeyboardButton(text=button[2], url=button[3]))
    return user_send_kb.adjust(1).as_markup()
async def admin_accept_start_send_keyboard(send_id):
    admin_accept_start_send_kb = InlineKeyboardBuilder()
    admin_accept_start_send_kb.add(InlineKeyboardButton(text='Начать рассылку',
                                                      callback_data=f'admin_accept_start_send_{send_id}'))
    admin_accept_start_send_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_send_{send_id}'))
    return admin_accept_start_send_kb.adjust(1).as_markup()
async def admin_sends_all_keyboard(sends, page: int = 0):
    admin_sends_all_kb = InlineKeyboardBuilder()
    len_sends = len(sends)
    sends = sends[page * 45:(page + 1) * 45]
    for send in sends:
        admin_sends_all_kb.row(InlineKeyboardButton(text=f'{send[1] if send[1] else "Медиа файл"}',
                                                   callback_data=f'admin_send_all_{send[0]}'))
    if page > 0 and len_sends > (page + 1) * 45:
        admin_sends_all_kb.add(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_all_{page + 1}'),
                               InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_all_{page - 1}'))
    elif len_sends > (page + 1) * 45:
        admin_sends_all_kb.add(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_all_{page + 1}'))
    elif page > 0:
        admin_sends_all_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_all_{page - 1}'))
    admin_sends_all_kb.row(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_sends_all_kb.as_markup()
async def admin_sends_vip_keyboard(sends, page: int = 0):
    len_sends = len(sends)
    sends = sends[page * 45:(page + 1) * 45]
    admin_sends_novip_kb = InlineKeyboardBuilder()
    for send in sends:
        admin_sends_novip_kb.row(InlineKeyboardButton(text=f'{send[1] if send[1] else "Медиа файл"}',
                                                      callback_data=f'admin_send_vip_{send[0]}'))
    if page > 0 and len_sends > (page + 1) * 45:
        admin_sends_novip_kb.add(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_vip_{page + 1}'),
                                 InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_vip_{page - 1}'))
    elif len_sends > (page + 1) * 45:
        admin_sends_novip_kb.add(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_vip_{page + 1}'))
    elif page > 0:
        admin_sends_novip_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_vip_{page - 1}'))
    admin_sends_novip_kb.row(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_sends_novip_kb.as_markup()
async def admin_sends_novip_keyboard(sends, page: int = 0):
    len_sends = len(sends)
    sends = sends[page*45:(page+1)*45]
    admin_sends_novip_kb = InlineKeyboardBuilder()
    for send in sends:
        admin_sends_novip_kb.row(InlineKeyboardButton(text=f'{send[1] if send[1] else "Медиа файл"}',
                                                    callback_data=f'admin_send_novip_{send[0]}'))
    if page > 0 and len_sends > (page + 1) * 45:
        admin_sends_novip_kb.add(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_novip_{page+1}'),
                                 InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_novip_{page-1}'))
    elif len_sends > (page + 1) * 45:
        admin_sends_novip_kb.add(InlineKeyboardButton(text='Вперед', callback_data=f'admin_sends_novip_{page+1}'))
    elif page > 0:
        admin_sends_novip_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_sends_novip_{page-1}'))
    admin_sends_novip_kb.row(InlineKeyboardButton(text='Назад', callback_data='admin_sends'))
    return admin_sends_novip_kb.as_markup()
async def admin_accept_send_all_keyboard(send_id):
    admin_accept_all_send_kb = InlineKeyboardBuilder()
    admin_accept_all_send_kb.add(InlineKeyboardButton(text='Начать рассылку сейчас',
                                                    callback_data=f'admin_accept_send_all_{send_id}'))
    admin_accept_all_send_kb.add(InlineKeyboardButton(text='Запланировать рассылку',
                                                      callback_data=f'admin_late_send_all_{send_id}'))
    admin_accept_all_send_kb.add(InlineKeyboardButton(text='Назначить отправку с интервалом',
                                                      callback_data=f'admin_interval_send_all_{send_id}'))
    admin_accept_all_send_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends_all'))
    return admin_accept_all_send_kb.adjust(1).as_markup()
async def admin_accept_send_vip_keyboard(send_id):
    admin_accept_vip_send_kb = InlineKeyboardBuilder()
    admin_accept_vip_send_kb.add(InlineKeyboardButton(text='Начать рассылку сейчас',
                                                    callback_data=f'admin_accept_send_vip_{send_id}'))
    admin_accept_vip_send_kb.add(InlineKeyboardButton(text='Запланировать рассылку',
                                                      callback_data=f'admin_late_send_vip_{send_id}'))
    admin_accept_vip_send_kb.add(InlineKeyboardButton(text='Назначить отправку с интервалом',
                                                      callback_data=f'admin_interval_send_vip_{send_id}'))
    admin_accept_vip_send_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends_vip'))
    return admin_accept_vip_send_kb.adjust(1).as_markup()
async def admin_accept_send_novip_keyboard(send_id):
    admin_accept_novip_send_kb = InlineKeyboardBuilder()
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Начать рассылку сейчас',
                                                        callback_data=f'admin_accept_send_novip_{send_id}'))
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Запланировать рассылку',
                                                        callback_data=f'admin_late_send_novip_{send_id}'))
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Назначить отправку с интервалом',
                                                        callback_data=f'admin_interval_send_novip_{send_id}'))
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends_novip'))
    return admin_accept_novip_send_kb.adjust(1).as_markup()
async def admin_accept_send_chats_keyboard(send_id):
    admin_accept_novip_send_kb = InlineKeyboardBuilder()
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Начать рассылку сейчас',
                                                        callback_data=f'admin_accept_send_chats_{send_id}'))
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Запланировать рассылку',
                                                        callback_data=f'admin_late_send_chats_{send_id}'))
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Назначить отправку с интервалом',
                                                        callback_data=f'admin_interval_send_chats_{send_id}'))
    admin_accept_novip_send_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_sends_chats'))
    return admin_accept_novip_send_kb.adjust(1).as_markup()
async def admin_loto_settings_keyboard():
    admin_loto_settings_kb = InlineKeyboardBuilder()
    admin_loto_settings_kb.add(InlineKeyboardButton(text='Моментальная лотерея',
                                                    callback_data='admin_moment_loto_settings'))
    admin_loto_settings_kb.add(InlineKeyboardButton(text='Ежедневная лотерея',
                                                    callback_data='admin_daily_loto_settings'))
    admin_loto_settings_kb.add(InlineKeyboardButton(text='Еженедельная лотерея',
                                                    callback_data='admin_weekly_loto_settings'))
    admin_loto_settings_kb.add(InlineKeyboardButton(text='Ежемесячная лотерея',
                                                    callback_data='admin_monthly_loto_settings'))
    admin_loto_settings_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_loto_settings_kb.adjust(1).as_markup()
async def admin_moment_loto_settings_keyboard():
    admin_moment_loto_settings_kb = InlineKeyboardBuilder()
    admin_moment_loto_settings_kb.add(InlineKeyboardButton(text='Изменить тип лотереи',
                                                           callback_data='admin_moment_change_chance'))
    admin_moment_loto_settings_kb.add(InlineKeyboardButton(text='Изменить минимальную ставку',
                                                           callback_data='admin_moment_min'))
    admin_moment_loto_settings_kb.add(InlineKeyboardButton(text='Изменить максимальную ставку',
                                                           callback_data='admin_moment_max'))
    admin_moment_loto_settings_kb.add(InlineKeyboardButton(text='Тест лотереи',
                                                           callback_data='admin_moment_test'))
    admin_moment_loto_settings_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_loto_settings'))
    return admin_moment_loto_settings_kb.adjust(1).as_markup()
async def admin_moment_loto_type_keyboard(type: str):
    kb = InlineKeyboardBuilder()
    if type != 'standart':
        kb.add(InlineKeyboardButton(text='Стандартная лотерея', callback_data='admin_moment_loto_type_standart'))
    if type != 'low':
        kb.add(InlineKeyboardButton(text='Низкий риск', callback_data='admin_moment_loto_type_low'))
    if type != 'hight':
        kb.add(InlineKeyboardButton(text='Высокий риск', callback_data='admin_moment_loto_type_hight'))
    if type != 'simple':
        kb.add(InlineKeyboardButton(text='Простая лотерея', callback_data='admin_moment_loto_type_simple'))
    if type != 'loser':
        kb.add(InlineKeyboardButton(text='Лузер', callback_data='admin_moment_loto_type_loser'))
    kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_moment_loto_settings'))
    return kb.adjust(1).as_markup()
async def admin_back_to_loto_settings_keyboard():
    admin_back_to_loto_settings_kb = InlineKeyboardBuilder()
    admin_back_to_loto_settings_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_moment_loto_settings'))
    return admin_back_to_loto_settings_kb.adjust(1).as_markup()






async def admin_daily_loto_settings_keyboard():
    admin_daily_loto_settings_kb = InlineKeyboardBuilder()
    admin_daily_loto_settings_kb.add(InlineKeyboardButton(text='Изменить стартовый капитал',
                                                          callback_data='admin_daily_change_count'))
    admin_daily_loto_settings_kb.add(InlineKeyboardButton(text='Изменить коэффициент умножения',
                                                          callback_data='admin_daily_change_coefficient'))
    admin_daily_loto_settings_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_loto_settings'))
    return admin_daily_loto_settings_kb.adjust(1).as_markup()
async def admin_weekly_loto_settings_keyboard():
    admin_weekly_loto_settings_kb = InlineKeyboardBuilder()
    admin_weekly_loto_settings_kb.add(InlineKeyboardButton(text='Изменить стартовый капитал',
                                                           callback_data='admin_weekly_change_count'))
    admin_weekly_loto_settings_kb.add(InlineKeyboardButton(text='Изменить коэффициент умножения',
                                                           callback_data='admin_weekly_change_coefficient'))
    admin_weekly_loto_settings_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_loto_settings'))
    return admin_weekly_loto_settings_kb.adjust(1).as_markup()
async def admin_monthly_loto_settings_keyboard():
    admin_monthly_loto_settings_kb = InlineKeyboardBuilder()
    admin_monthly_loto_settings_kb.add(InlineKeyboardButton(text='Изменить стартовый капитал',
                                                            callback_data='admin_monthly_change_count'))
    admin_monthly_loto_settings_kb.add(InlineKeyboardButton(text='Изменить коэффициент умножения',
                                                            callback_data='admin_monthly_change_coefficient'))
    admin_monthly_loto_settings_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_loto_settings'))
    return admin_monthly_loto_settings_kb.adjust(1).as_markup()
async def admin_update_balance_keyboard():
    admin_update_balance_kb = InlineKeyboardBuilder()
    admin_update_balance_kb.add(InlineKeyboardButton(text='Добавить/отнять сумму', callback_data='admin_u_b'))
    admin_update_balance_kb.add(InlineKeyboardButton(text='Установить значение', callback_data='admin_s_b'))
    admin_update_balance_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_update_balance_kb.adjust(1).as_markup()
async def admin_shablon_prizes_keyboard(prizes, game_id):
    admin_shablon_prizes_kb = InlineKeyboardBuilder()
    if prizes:
        if len(prizes) > 20:
            prizes = prizes[:20]
        for prize in prizes:
            admin_shablon_prizes_kb.add(InlineKeyboardButton(text=prize[1],
                                                             callback_data=f'admin_shablon_add_{prize[0]}_{game_id}'))
    admin_shablon_prizes_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_game_prizes_{game_id}'))
    return admin_shablon_prizes_kb.adjust(1).as_markup()
async def admin_history_keyboard(games: list):
    admin_history_kb = InlineKeyboardBuilder()
    games = games[::-1]
    if len(games) > 20:
        games = games[:19]
    for game in games:
        admin_history_kb.add(InlineKeyboardButton(text=f'Игра {game[1]}', callback_data=f'admin_history_{game[0]}'))
    admin_history_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_history_kb.adjust(1).as_markup()

async def admin_new_game():
    admin_new_game_kb = InlineKeyboardBuilder()
    admin_new_game_kb.add(InlineKeyboardButton(text='Отмена', callback_data='admin_new_game_cancel'))
    return admin_new_game_kb.adjust(1).as_markup()
async def admin_canc_game_keyboard(game_id):
    admin_canc_game_kb = InlineKeyboardBuilder()
    admin_canc_game_kb.add(InlineKeyboardButton(text='Отменить игру', callback_data=f'admin_cancel_game_{game_id}'))
    admin_canc_game_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_current_game'))
    return admin_canc_game_kb.adjust(1).as_markup()
async def admin_send_end_game(game_id):
    admin_send_end_game_kb = InlineKeyboardBuilder()
    admin_send_end_game_kb.add(InlineKeyboardButton(text='Сообщить об отмене игры?',
                                                    callback_data=f'admin_send_end_{game_id}'))
    admin_send_end_game_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_send_end_game_kb.adjust(1).as_markup()

async def current_game_keyboard(game):
    current_game_kb = InlineKeyboardBuilder()
    if game[4] == 0:
        current_game_kb.add(InlineKeyboardButton(text='Начать игру', callback_data=f'admin_start_game_{game[0]}'))
    else:
        current_game_kb.add(InlineKeyboardButton(text='Завершить игру досрочно',
                                                 callback_data=f'admin_end_game_{game[0]}'))
        current_game_kb.add(InlineKeyboardButton(text='Участники игры', callback_data=f'admin_users_game_{game[0]}'))
        current_game_kb.add(InlineKeyboardButton(text='Отменить игру', callback_data=f'admin_canc_game_{game[0]}'))
    current_game_kb.add(InlineKeyboardButton(text='Призы', callback_data=f'admin_game_prizes_{game[0]}'))
    if game[4] == 0:
        current_game_kb.add(InlineKeyboardButton(text='Удалить игру', callback_data=f'admin_del_game_{game[0]}'))
    current_game_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return current_game_kb.adjust(1).as_markup()
async def user_game_keyboard(game_id: int):
    user_game_kb = InlineKeyboardBuilder()
    user_game_kb.add(InlineKeyboardButton(text='✨  Участвовать', callback_data=f'user_game_{game_id}'))
    return user_game_kb.adjust(1).as_markup()
async def user_menu(user_id):
    user_menu_kb = InlineKeyboardBuilder()
    user = await get_user(user_id)
    game = await get_active_game()
    unread_count = await get_unread_messages_count(user_id)
    if game:
        user_menu_kb.add(InlineKeyboardButton(text='🎁  Призы текущей игры', callback_data='user_prizes'))
    if user[10] != '':
        if datetime.datetime.isoformat(datetime.datetime.now()) >= user[10]:
            user_menu_kb.add(InlineKeyboardButton(text='🎇  Купить VIP подписку', callback_data='buy_vip'))
        else:
            user_menu_kb.add(InlineKeyboardButton(text='💵  Вывод средств', callback_data='get_cash'))
            user_menu_kb.add(InlineKeyboardButton(text='📲  Передача средств', callback_data='send_cash'))
    else:
        user_menu_kb.add(InlineKeyboardButton(text='🎇  Купить VIP подписку', callback_data='buy_vip'))
    user_menu_kb.add(InlineKeyboardButton(text='💰  Пополнение счёта  ', callback_data='buy_cash'))
    if user[9] > 0:
        user_menu_kb.add(InlineKeyboardButton(text='🎰  Моментальная лотерея', callback_data='moment_loto'))
    else:
        user_menu_kb.add(InlineKeyboardButton(text='🔒  Моментальная лотерея (пополните баланс чтобы сыграть)',
                                              callback_data='moment_block'))
    if user[11] >= 10 and user[9] > 0:
        user_menu_kb.add(InlineKeyboardButton(text='🗓  Билеты на лотереи', callback_data='loto_tickets'))
    elif user[9] <= 0:
        user_menu_kb.add(InlineKeyboardButton(text='🔒  Лотереи (пополните баланс, чтобы получить билеты)',
                                              callback_data='loto_block_1'))
    elif user[11] < 10:
        user_menu_kb.add(InlineKeyboardButton(text='🔒  Лотереи (необходимо сиграть 10+ моментальных лотерей)',
                                              callback_data='loto_block_2'))
    if user[12] == 0:
        user_menu_kb.add(InlineKeyboardButton(text='🕶  Сделать анонимным', callback_data='user_anonim'))
    else:
        user_menu_kb.add(InlineKeyboardButton(text='👁‍🗨  Сделать видимым', callback_data='user_visible'))
    user_menu_kb.add(InlineKeyboardButton(text='📅  Подписка на бота', callback_data='user_subscribe'))
    user_menu_kb.add(InlineKeyboardButton(text='🗺  Бесплатный адрес', callback_data='referrer'))
    user_menu_kb.add(InlineKeyboardButton(text=f'📬{"("+str(unread_count)+")" if unread_count > 0 else ""}  Почта',
                                          callback_data='user_mail'))
    user_menu_kb.add(InlineKeyboardButton(text='💸  Пожертвования проекту', callback_data='user_donate'))
    user_menu_kb.add(InlineKeyboardButton(text='🙋‍♂️  Помощ и поддержка', callback_data='user_help'))
    return user_menu_kb.adjust(1).as_markup()
async def user_help_keyboard():
    user_help_kb = InlineKeyboardBuilder()
    user_help_kb.add(InlineKeyboardButton(text='❔  Часто задаваемые вопросы', callback_data='user_questions'))
    user_help_kb.add(InlineKeyboardButton(text='📑  Помощь с использованием', callback_data='user_use'))
    user_help_kb.add(InlineKeyboardButton(text='📞  Связаться с администратором', callback_data='user_contact'))
    user_help_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_menu'))
    return user_help_kb.adjust(1).as_markup()
async def back_to_help_keyboard():
    back_to_help_kb = InlineKeyboardBuilder()
    back_to_help_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_help'))
    back_to_help_kb.add(InlineKeyboardButton(text='🔚  Меню', callback_data='user_menu'))
    return back_to_help_kb.adjust(1).as_markup()
async def captcha_keyboard(list):
    captcha_kb = InlineKeyboardBuilder()
    for i in list:
        captcha_kb.add(InlineKeyboardButton(text=i[1:] if i[0] == '1' else i,
                                            callback_data=f'captcha_{i[0] if i[0] == "1" else "0"}'))
    return captcha_kb.adjust(3).as_markup()



async def user_accept_donate_keyboard():
    user_accept_donate_kb = InlineKeyboardBuilder()
    user_accept_donate_kb.add(InlineKeyboardButton(text='✅  Поддержать проект', callback_data='user_accept_donate'))
    user_accept_donate_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_menu'))
    return user_accept_donate_kb.adjust(1).as_markup()
async def user_mail_keyboard(unread_count):
    admin_messages_kb = InlineKeyboardBuilder()
    admin_messages_kb.add(
        InlineKeyboardButton(text=f'{"(" + str(unread_count) + ")" if unread_count > 0 else ""}📬  Входящие сообщения',
                             callback_data='user_messages_post'))
    admin_messages_kb.add(InlineKeyboardButton(text='💬  Отправить сообщение администратору',
                                               callback_data='user_messages_send'))
    admin_messages_kb.add(InlineKeyboardButton(text='Назад', callback_data='user_menu'))
    return admin_messages_kb.adjust(1).as_markup()
async def user_answer_keyboard(sender_id):
    user_answer_kb = InlineKeyboardBuilder()
    user_answer_kb.add(InlineKeyboardButton(text='💬  Ответить', callback_data=f'user_messages_to_{sender_id}'))
    user_answer_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_mail'))
    return user_answer_kb.adjust(1).as_markup()



async def user_messages_post_keyboard(messages, unread_messages, user_id):
    admin_messages_post_kb = InlineKeyboardBuilder()
    for message in messages:
        for user in unread_messages:
            if message[1] in user:
                count = await get_unread_messages_count_from_sender(user_id, message[1])
                sender = await get_user(message[1])
                admin_messages_post_kb.add(InlineKeyboardButton(text=
                                                            f'💬{"("+str(count)+")"}  '
                                                            f'От {sender[1] if sender[1] else sender[2]}',
                                                            callback_data=f'user_messages_from_{message[1]}'))
                break
        else:
            sender = await get_user(message[1])
            admin_messages_post_kb.add(InlineKeyboardButton(text=f'💬  От {sender[1] if sender[1] else sender[2]}',
                                                            callback_data=f'user_messages_from_{message[1]}'))
    admin_messages_post_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_mail'))
    return admin_messages_post_kb.adjust(1).as_markup()
async def user_messages_from_keyboard(messages):
    admin_messages_from_kb = InlineKeyboardBuilder()
    for message in messages:
        admin_messages_from_kb.add(InlineKeyboardButton(text=f'{"* " if message[5] == 0 else ""}'+message[4],
                                                        callback_data=f'user_message_{message[0]}'))
    admin_messages_from_kb.add(InlineKeyboardButton(text='Назад', callback_data='user_messages_post'))
    return admin_messages_from_kb.adjust(1).as_markup()

async def user_messages_send_keyboard(admins_ids):
    user_messages_send_kb = InlineKeyboardBuilder()
    for admin_id in admins_ids:
        admin = await get_user(admin_id)
        if not admin:
            continue
        user_messages_send_kb.add(InlineKeyboardButton(text=f'🙋‍♂️  Администратор {admin[1] if admin[1] else admin[2]}',
                                                      callback_data=f'user_messages_to_{admin_id}'))
    user_messages_send_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_mail'))
    return user_messages_send_kb.adjust(1).as_markup()
async def user_back_to_messages_keyboard():
    user_back_to_messages_kb = InlineKeyboardBuilder()
    user_back_to_messages_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_mail'))
    return user_back_to_messages_kb.adjust(1).as_markup()
async def user_accept_message_keyboard():
    user_accept_message_kb = InlineKeyboardBuilder()
    user_accept_message_kb.add(InlineKeyboardButton(text='✅  Отправить', callback_data='user_accept_message'))
    user_accept_message_kb.add(InlineKeyboardButton(text='🔙  Отмена', callback_data='user_mail'))
    return user_accept_message_kb.adjust(1).as_markup()
async def user_accept_reply_keyboard():
    user_accept_reply_message_kb = InlineKeyboardBuilder()
    user_accept_reply_message_kb.add(InlineKeyboardButton(text='✅  Отправить',
                                                          callback_data='user_accept_reply_message'))
    user_accept_reply_message_kb.add(InlineKeyboardButton(text='🔙  Отмена', callback_data='user_mail'))
    return user_accept_reply_message_kb.adjust(1).as_markup()
async def user_message_keyboard(message):
    user_message_kb = InlineKeyboardBuilder()
    user_message_kb.add(InlineKeyboardButton(text='💬  Ответить', callback_data=f'user_reply_message_{message[0]}'))
    user_message_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data=f'user_messages_from_{message[2]}'))
    return user_message_kb.adjust(1).as_markup()
async def admin_moderators_keyboard():
    admin_moderators_kb = InlineKeyboardBuilder()
    admin_moderators_kb.add(InlineKeyboardButton(text='Список модераторов', callback_data='admin_list_moderators'))
    admin_moderators_kb.add(InlineKeyboardButton(text='Добавить модератора', callback_data='admin_add_moderator'))
    admin_moderators_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_moderators_kb.adjust(1).as_markup()
async def admin_list_moderators_keyboard(moderators):
    admin_list_moderators_kb = InlineKeyboardBuilder()
    for mdr in moderators:
        moderator = await get_user(mdr)
        if moderator:
            admin_list_moderators_kb.add(InlineKeyboardButton(text=f'{moderator[1] if moderator[1] else moderator[2]}',
                                                              callback_data=f'admin_moderator_{mdr}'))
    admin_list_moderators_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_moderators'))
    return admin_list_moderators_kb.adjust(1).as_markup()
async def admin_moderator_keyboard(moderator_id):
    admin_moderator_kb = InlineKeyboardBuilder()
    admin_moderator_kb.add(InlineKeyboardButton(text='Удалить модератора',
                                                callback_data=f'admin_delete_moderator_{moderator_id}'))
    admin_moderator_kb.add(InlineKeyboardButton(text='Сделать админом',
                                                callback_data=f'admin_make_admin_{moderator_id}'))
    admin_moderator_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_list_moderators'))
    return admin_moderator_kb.adjust(1).as_markup()
async def admin_accept_delete_moderator_keyboard(moderator_id):
    admin_accept_delete_moderator_kb = InlineKeyboardBuilder()
    admin_accept_delete_moderator_kb.add(InlineKeyboardButton(text='Подтвердить удаление',
                                                        callback_data=f'admin_accept_delete_moderator_{moderator_id}'))
    admin_accept_delete_moderator_kb.add(InlineKeyboardButton(text='Назад',
                                                              callback_data=f'admin_moderator_{moderator_id}'))
    return admin_accept_delete_moderator_kb.adjust(1).as_markup()
async def admin_accept_make_admin_keyboard(moderator_id):
    admin_accept_make_admin_kb = InlineKeyboardBuilder()
    admin_accept_make_admin_kb.add(InlineKeyboardButton(text='Подтвердить назначение',
                                                        callback_data=f'admin_accept_make_admin_{moderator_id}'))
    admin_accept_make_admin_kb.add(InlineKeyboardButton(text='Назад',
                                                        callback_data=f'admin_moderator_{moderator_id}'))
    return admin_accept_make_admin_kb.adjust(1).as_markup()
async def admin_back_to_moderators_keyboard():
    admin_back_to_moderators_kb = InlineKeyboardBuilder()
    admin_back_to_moderators_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_moderators'))
    return admin_back_to_moderators_kb.adjust(1).as_markup()
async def admin_accept_moderator_keyboard():
    admin_accept_moderator_kb = InlineKeyboardBuilder()
    admin_accept_moderator_kb.add(InlineKeyboardButton(text='Подтвердить добавление',
                                                       callback_data='admin_accept_moderator'))
    admin_accept_moderator_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_moderators'))
    return admin_accept_moderator_kb.adjust(1).as_markup()



async def loto_tickets_keyboard(user):
    loto_tickets_kb = InlineKeyboardBuilder()
    daily = await get_daily_users_count()
    weekly = await get_weekly_users_count()
    monthly = await get_monthly_users_count()
    if not await check_daily_user(user[0]):
        if user[11] >= 10 and user[9] >= 500:
            loto_tickets_kb.add(InlineKeyboardButton(text=f'⏳  Ежедневная лотерея - 500 ({daily[0]} пользователей)',
                                                     callback_data='t_ticket_daily'))
        else:
            loto_tickets_kb.add(InlineKeyboardButton(text=f'🔒  Ежедневная лотерея - 500 ({daily[0]} пользователей)',
                                                     callback_data='no_data'))
    else:
        loto_tickets_kb.add(InlineKeyboardButton(text=f'✅  Вы учатник ежедневной лотереи ({daily[0]} пользователей)',
                                             callback_data='no_data'))
    if not await check_weekly_user(user[0]):
        if user[9] >= 1000 and user[11] >= 50:
            loto_tickets_kb.add(InlineKeyboardButton(text=f'🎫  Еженедельная лотерея - 1000 ({weekly[0]} пользователей)',
                                                     callback_data='t_ticket_weekly'))
        else:
            loto_tickets_kb.add(InlineKeyboardButton(text=f'🔒  Еженедельная лотерея - 1000 ({weekly[0]} пользователей)',
                                                     callback_data='no_data'))
    else:
        loto_tickets_kb.add(InlineKeyboardButton(text=f'✅  Вы учатник еженедельной лотереи ({weekly[0]} пользователей)',
                                                 callback_data='no_data'))
    if not await check_monthly_user(user[0]):
        if user[9] >= 4000 and user[11] >= 100:
            loto_tickets_kb.add(InlineKeyboardButton(text=f'🗓  Ежемесячная лотерея - 4000 ({monthly[0]} пользователей)',
                                                     callback_data='t_ticket_monthly'))
        else:
            loto_tickets_kb.add(InlineKeyboardButton(text=f'🔒  Ежемесячная лотерея - 4000 ({monthly[0]} пользователей)',
                                                     callback_data='no_data'))
    else:
        loto_tickets_kb.add(InlineKeyboardButton(text=f'✅  Вы учатник ежемесячной лотереи ({monthly[0]} пользователей)',
                                                 callback_data='no_data'))
    loto_tickets_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_menu'))
    return loto_tickets_kb.adjust(1).as_markup()
async def admin_addresses_keyboard(addresses: list):
    admin_addresses_kb = InlineKeyboardBuilder()
    if addresses:
        for address in addresses:
            if address[3] == 1:
                text = f'(Доступен) {address[1]}'
            else:
                text = f'(Недоступен) {address[1]}'
            if address[2] != 0:
                user = await get_user(address[2])
                if user[1]:
                    text = f'(Активирован @{user[1]}) {address[1]} '
                else:
                    text = f'(Активирован {user[2]}) {address[1]} '

            admin_addresses_kb.add(InlineKeyboardButton(text=text,
                                                        callback_data=f'admin_address_select_{address[0]}'))
    admin_addresses_kb.add(InlineKeyboardButton(text='Добавить промокод', callback_data='admin_add_address'))
    admin_addresses_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_addresses_kb.adjust(1).as_markup()
async def admin_address_select_keyboard(address_id):
    admin_address_select_kb = InlineKeyboardBuilder()
    address = await get_address(address_id)
    if address[3] == 1:
        admin_address_select_kb.add(InlineKeyboardButton(text='Деактивировать промокод',
                                                         callback_data=f'admin_address_deactivate_{address[0]}'))
    else:
        admin_address_select_kb.add(InlineKeyboardButton(text='Активировать промокод',
                                                         callback_data=f'admin_address_activate_{address[0]}'))
    admin_address_select_kb.add(InlineKeyboardButton(text='Удалить промокод',
                                                     callback_data=f'admin_address_delete_{address[0]}'))
    admin_address_select_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_addresses'))
    return admin_address_select_kb.adjust(1).as_markup()
async def user_back_keyboard():
    user_back_kb = InlineKeyboardBuilder()
    user_back_kb.add(InlineKeyboardButton(text='Назад', callback_data='user_menu'))
    return user_back_kb.adjust(1).as_markup()
async def admin_prizes_keyboard(prizes: list, game_id):
    admin_prizes_kb = InlineKeyboardBuilder()
    for prize in prizes:
        admin_prizes_kb.add(InlineKeyboardButton(text=f'{prize[1]} - {prize[3]}шт',
                                                 callback_data=f'admin_current_prize_{prize[0]}'))
    admin_prizes_kb.add(InlineKeyboardButton(text='Добавить новый приз', callback_data=f'admin_add_prize_{game_id}'))
    admin_prizes_kb.add(InlineKeyboardButton(text='Шаблоны призов', callback_data=f'admin_shablon_prize_{game_id}'))
    admin_prizes_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_current_game'))
    admin_prizes_kb.add(InlineKeyboardButton(text='Выйти в меню', callback_data='admin_menu'))
    return admin_prizes_kb.adjust(1).as_markup()
async def user_prizes_keyboard(prizes: list, user_id: int, game_id: int):
    user = await get_game_user(game_id, user_id)
    user_prizes_kb = InlineKeyboardBuilder()
    if user:
        user_prizes_kb.add(InlineKeyboardButton(text='✅  Вы уже учавствуете', callback_data='no_data'))
    else:
        user_prizes_kb.add(InlineKeyboardButton(text='✏  Учавствовать', callback_data=f'user_game_{game_id}'))
    user_prizes_kb.add(InlineKeyboardButton(text='🔙 Назад', callback_data='user_menu'))
    return user_prizes_kb.adjust(1).as_markup()
async def admin_back_keyboard():
    admin_back_kb = InlineKeyboardBuilder()
    admin_back_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_menu'))
    return admin_back_kb.adjust(1).as_markup()
async def admin_current_prize_keyboard(prize_id):
    admin_current_prize_kb = InlineKeyboardBuilder()
    prize = await get_prize(prize_id)
    admin_current_prize_kb.add(InlineKeyboardButton(text='Изменить текст призов',
                                                    callback_data=f'admin_text_prize_{prize_id}'))
    admin_current_prize_kb.add(InlineKeyboardButton(text='Изменить количество призов',
                                                    callback_data=f'admin_count_prize_{prize_id}'))
    admin_current_prize_kb.add(InlineKeyboardButton(text='Удалить выбранный приз',
                                                    callback_data=f'admin_del_prize_{prize_id}'))
    admin_current_prize_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_game_prizes_{prize[2]}'))
    admin_current_prize_kb.add(InlineKeyboardButton(text='Выйти в меню', callback_data='admin_menu'))
    return admin_current_prize_kb.adjust(1).as_markup()
async def admin_text_prize_keyboard(prize_id):
    admin_text_prize_kb = InlineKeyboardBuilder()
    admin_text_prize_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_current_prize_{prize_id}'))
    admin_text_prize_kb.add(InlineKeyboardButton(text='Выйти в меню', callback_data='admin_menu'))
    return admin_text_prize_kb.adjust(1).as_markup()
async def admin_game_prize_keyboard():
    admin_text_prize_kb = InlineKeyboardBuilder()
    admin_text_prize_kb.add(InlineKeyboardButton(text='Назад', callback_data=f'admin_current_game'))
    admin_text_prize_kb.add(InlineKeyboardButton(text='Выйти в меню', callback_data='admin_menu'))
    return admin_text_prize_kb.adjust(1).as_markup()
async def admin_end_game(game_id):
    admin_ending_kb = InlineKeyboardBuilder()
    admin_ending_kb.add(InlineKeyboardButton(text='Завершить игру', callback_data=f'admin_ending_game_{game_id}'))
    admin_ending_kb.add(InlineKeyboardButton(text='Назад', callback_data='admin_current_game'))
    admin_ending_kb.add(InlineKeyboardButton(text='Выйти в меню', callback_data='admin_menu'))
    return admin_ending_kb.adjust(1).as_markup()
async def moment_loto_keyboard():
    moment_loto_kb = InlineKeyboardBuilder()
    moment_loto_kb.add(InlineKeyboardButton(text='🎲  Играть', callback_data='moment_loto_hell'))
    moment_loto_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_menu'))
    return moment_loto_kb.adjust(1).as_markup()
async def moment_loto_value_keyboard():
    moment_loto_value_kb = InlineKeyboardBuilder()
    moment_loto_value_kb.add(InlineKeyboardButton(text='✅  Подтвердить', callback_data='m_loto_confirm'))
    moment_loto_value_kb.add(InlineKeyboardButton(text='🔙  Назад', callback_data='user_menu'))
    return moment_loto_value_kb.adjust(1).as_markup()
async def bot_url():
    bot_url_kb = InlineKeyboardBuilder()
    bot_url_kb.add(InlineKeyboardButton(text='📲  Перейти в бота', url=f'tg://resolve?domain={BOT_USERNAME}'))
    return bot_url_kb.adjust(1).as_markup()