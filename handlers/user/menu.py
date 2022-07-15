
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from loader import dp
from filters import IsAdmin, IsUser

catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Тапсырыс жайлы ақпарат'

settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'
send_message = 'Рассылка'
stats = 'Статистика'

@dp.message_handler(IsAdmin(), commands='menu')
async def admin_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, orders)
    markup.add(send_message, stats)

    await message.answer('Меню', reply_markup=markup)

@dp.message_handler(IsUser(), commands='menu')
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    markup.add(cart)
    markup.add(delivery_status)

    await message.answer('Меню', reply_markup=markup)
