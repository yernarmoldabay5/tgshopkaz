
import os
import handlers
from aiogram import executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import config
from loader import dp, db, bot
import filters
import logging

filters.setup(dp)

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 5000))
user_message = 'Пользователь'
admin_message = 'Админ'


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    #markup.row(user_message, admin_message)

    await message.answer('''Сәлем! 👋

🤖 Бұл - телеграм бот интернет дүкені 
    
🛍️ Мәзірге өту үшін /menu батырмасын басыңыз.

💰 Бот арқылы тауар сатып алу - менеджер арқылы жүзеге асады. Яғни қауіпсіз төлем арқылы жұмыс жасаймыз.

❓ Сұрақтарыңыз болса, немесе бот істемесе Команда /sos-ты басып админға шықсаңыз болады! 

🤝 Тура осындай бот жасатамын десеңіз, бізге хабарласыңыз <a href="https://t.me/arslan_toilybay">Arslan Toilybay</a>)))
    ''', reply_markup=markup)

    print(message.chat.id)
    db.query('INSERT INTO clients VALUES (' + str(message.chat.id) + ')')


@dp.message_handler(text=user_message)
async def user_mode(message: types.Message):

    cid = message.chat.id
    if cid in config.ADMINS:
        config.ADMINS.remove(cid)

    await message.answer('Включен пользовательский режим.', reply_markup=ReplyKeyboardRemove())


@dp.message_handler(text=admin_message)
async def admin_mode(message: types.Message):

    cid = message.chat.id
    if cid not in config.ADMINS:
        config.ADMINS.append(cid)

    await message.answer('Включен админский режим.', reply_markup=ReplyKeyboardRemove())


async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
    db.create_tables()

    await bot.delete_webhook()
    await bot.set_webhook(config.WEBHOOK_URL)


async def on_shutdown():
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")


if __name__ == '__main__':

    if "HEROKU" in list(os.environ.keys()):

        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )

    else:

        executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
