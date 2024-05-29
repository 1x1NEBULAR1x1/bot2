import asyncio
import datetime

from aiogram.client.bot import Bot
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMINS_IDS, MONTHLY_LOTO, WEEKLY_LOTO, DAILY_LOTO, CHATS_IDS
from db import (create_tables, daily_winner, set_new_daily_loto, get_daily_users, update_balance, weekly_winner,
                get_weekly_users, set_new_weekly_loto, set_new_monthly_loto, monthly_winner, get_monthly_users,
                set_monthly_loto, set_weekly_loto, set_daily_loto, get_user, get_monthly_moment_loto,
                get_daily_moment_loto, deactivate_sends, get_time_limit, get_users)
from heandlers import heandlers
from callbacks import callbacks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import keyboards as kb



async def process_daily_loto(bot: Bot):
    winner = await daily_winner()
    if not winner:
        await set_new_daily_loto()
        return
    users = await get_daily_users()
    daily_loto = await get_daily_moment_loto()
    value = DAILY_LOTO[0] + daily_loto[0] * DAILY_LOTO[1]
    await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Поздравляем, вы победили в ежедневной лотерее! </b>\n'
                                                   f'✨  <b>Ваш выигрыш: {value}</b>!',
                           reply_markup=await kb.user_back_keyboard())
    await asyncio.sleep(0.05)
    await update_balance(winner[0], value)
    await bot.send_message(chat_id=ADMINS_IDS[0], text=f'<b>⏳  Победитель дня: {winner[1]} - {value}</b>',
                           reply_markup=await kb.admin_back_keyboard())
    await asyncio.sleep(0.05)
    for user in users:
        if user != winner[0]:
            winner_user = await get_user(winner[0])
            if winner_user[12] == 1:
                winner_username = '🕶  Анонимный пользователь'
            else:
                winner_username = f'@{winner_user[1]}'
            await bot.send_message(chat_id=user, text=f'✨  <b>Ежедневная лотерея завершена, победитель дня: \n'
                                                      f'{winner_username}</b>',
                                   reply_markup=await kb.user_back_keyboard())
            await asyncio.sleep(0.06)
    for chat in CHATS_IDS:
        winner_user = await get_user(winner[0])
        if winner_user[12] == 1:
            winner_username = '🕶  Анонимный пользователь'
        else:
            winner_username = f'@{winner_user[1]}'
        await bot.send_message(chat_id=chat, text=f'🎉  <b>Поздравляем, победитель дня: \n{winner_username}</b>',
                               reply_markup=await kb.bot_url())
        await asyncio.sleep(0.05)
    await set_new_daily_loto()
async def process_weekly_loto(bot: Bot):
    winner = await weekly_winner()
    if not winner:
        await set_new_weekly_loto()
        return
    users = await get_weekly_users()
    weekly_loto = await get_daily_moment_loto()
    value = WEEKLY_LOTO[0] + weekly_loto[0] * WEEKLY_LOTO[1]
    winner_user = await get_user(winner[0])
    if winner_user[12] == 1:
        winner_username = '🕶  Анонимный пользователь'
    else:
        winner_username = f'@{winner_user[1]}'
    await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Поздравляем, вы победили в еженедельной лотерее! </b>\n'
                                                   f'✨  <b>Ваш выигрыш: {value}</b>!',
                           reply_markup=await kb.user_back_keyboard())
    await asyncio.sleep(0.05)
    await update_balance(winner[0], value)
    await bot.send_message(chat_id=ADMINS_IDS[0], text=f'<b>⏳  Победитель недели: {winner_username} - {value}</b>',
                           reply_markup=await kb.admin_back_keyboard())
    await asyncio.sleep(0.05)
    for user in users:
        if user != winner[0]:
            await bot.send_message(chat_id=user, text=f'✨  <b>Еженедельная лотерея завершена, \nпобедитель недели: '
                                   f'{winner_username}</b>', reply_markup=await kb.user_back_keyboard())
            await asyncio.sleep(0.06)
    for chat in CHATS_IDS:
        winner_user = await get_user(winner[0])
        if winner_user[12] == 1:
            winner_username = '🕶  Анонимный пользователь'
        else:
            winner_username = f'@{winner_user[1]}'
        await bot.send_message(chat_id=chat, text=f'🎉  <b>Поздравляем, победитель недели: \n{winner_username}</b>',
                               reply_markup=await kb.bot_url())
        await asyncio.sleep(0.05)
    await set_new_weekly_loto()
async def process_monthly_loto(bot: Bot):
    winner = await monthly_winner()
    if not winner:
        await set_new_monthly_loto()
        return
    users = await get_monthly_users()
    monthly_loto = await get_monthly_moment_loto()
    value = MONTHLY_LOTO[0] + monthly_loto[0] * MONTHLY_LOTO[1]
    await bot.send_message(chat_id=winner[0], text=f'🎉  <b>Поздравляем, вы победили в ежемесячной лотерее! </b>\n'
                                                   f'✨  <b>Ваш выигрыш: {value}</b>!',
                           reply_markup=await kb.user_back_keyboard())
    await asyncio.sleep(0.05)
    await update_balance(winner[0], value)
    winner_user = await get_user(winner[0])
    await bot.send_message(chat_id=ADMINS_IDS[0], text=f'<b>⏳  Победитель месяца: {winner_user[1]} - {value}</b>',
                           reply_markup=await kb.admin_back_keyboard())
    await asyncio.sleep(0.05)
    for user in users:
        if user != winner[0]:
            winner_user = await get_user(winner[0])
            if winner_user[12] == 1:
                winner_username = '🕶  Анонимный пользователь'
            else:
                winner_username = f'@{winner_user[1]}'
            await bot.send_message(chat_id=user, text=f'✨  <b>Ежемесячная лотерея завершена, победитель месяца:\n'
                                   f'{winner_username}</b>', reply_markup=await kb.user_back_keyboard())
            await asyncio.sleep(0.06)
    await set_new_monthly_loto()
    for chat in CHATS_IDS:
        winner_user = await get_user(winner[0])
        if winner_user[12] == 1:
            winner_username = '🕶  Анонимный пользователь'
        else:
            winner_username = f'@{winner_user[1]}'
        await bot.send_message(chat_id=chat, text=f'🎉  <b>Поздравляем, победитель месяца: \n{winner_username}</b>',
                               reply_markup=await kb.bot_url())
        await asyncio.sleep(0.05)
async def process_time_checker(bot: Bot):
    users = await get_users()
    for user in users:
        user = await get_user(user[0])
        if user[3] == str((datetime.datetime.now() + datetime.timedelta(days=3)).date()):
            await bot.send_message(chat_id=user[0], text='🕒  <b>Через 3 дня заканчивается ваша подписка на бота, '
                                                         'для продления напишите администратору</b>',
                                   reply_markup=await kb.admin_url_keyboard())
async def start():
    print('start')
async def shutdown():
    await deactivate_sends()
    print('shutdown')
async def main():
    bot = Bot(token=TOKEN, parse_mode='HTML')
    await create_tables()
    await set_monthly_loto()
    await set_weekly_loto()
    await set_daily_loto()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process_time_checker, trigger='cron', hour=18, minute=0, start_date=datetime.datetime.now(),
                      kwargs={'bot': bot})
    scheduler.add_job(process_daily_loto, trigger='cron', hour=0, minute=0, start_date=datetime.datetime.now(),
                      kwargs={'bot': bot})
    scheduler.add_job(process_weekly_loto, trigger='cron', day_of_week='mon', hour=0, minute=0,
                      start_date=datetime.datetime.now(), kwargs={'bot': bot})
    scheduler.add_job(process_monthly_loto, trigger='cron', day=1, hour=0, minute=0, start_date=datetime.datetime.now(),
                      kwargs={'bot': bot})
    scheduler.start()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    limit = 0.5
    if await get_time_limit():
        limit = float((await get_time_limit())[0])
    from middlewares import AntiFloodMiddleware
    dp.message.middleware.register(AntiFloodMiddleware(limit))
    dp.callback_query.middleware.register(AntiFloodMiddleware(limit))
    dp.startup.register(start)
    dp.shutdown.register(shutdown)
    dp.include_routers(heandlers, callbacks)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, scheduler=scheduler)
    finally:
        await bot.session.close()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Exit')
