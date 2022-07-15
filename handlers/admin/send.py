from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from filters import IsAdmin
from handlers.user.menu import send_message
from loader import dp, db, bot
from states.sos_state import SendState

send_cb = CallbackData('send', 'action')

@dp.message_handler(IsAdmin(), text=send_message)
async def process_send(message: Message):
    await message.answer("Выберите категорию подписчиков для рассылки", reply_markup=construct_send_markup())

@dp.callback_query_handler(IsAdmin(), send_cb.filter(action='ALL'))
@dp.callback_query_handler(IsAdmin(), send_cb.filter(action='PAYER'))
@dp.callback_query_handler(IsAdmin(), send_cb.filter(action='REJECTER'))
@dp.callback_query_handler(IsAdmin(), send_cb.filter(action='NOT'))
async def payment_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    action = callback_data['action']
    all_id_list = db.fetchall('SELECT distinct(cid) FROM clients')
    await state.update_data(action=action)
    await state.update_data(ids=all_id_list)
    await SendState.message.set()
    await bot.send_message(query.message.chat.id, "Пришлите сообщение, текст, фото/видео рассылки.")


@dp.message_handler(IsAdmin(), state=SendState.message, content_types=["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location", "contact"])
async def process_address(message: Message, state: FSMContext):
    data = await state.get_data()
    for id in data['ids']:
        await message.send_copy(id[0])
    await state.finish()



def construct_send_markup():
    send_markup = InlineKeyboardMarkup()
    all_btn = InlineKeyboardButton('Всем юзерам, которые зашли в бот', callback_data=send_cb.new(action='ALL'))
    payer_btn = InlineKeyboardButton('Юзерам, купивщим товар', callback_data=send_cb.new(action='PAYER'))
    rejecter_btn = InlineKeyboardButton('Юзерам, отказавщихся при оплате', callback_data=send_cb.new(action='REJECTER'))
    not_btn = InlineKeyboardButton('Неактивным юзерам', callback_data=send_cb.new(action='NOT'))
    send_markup.add(all_btn)
    send_markup.add(payer_btn)
    send_markup.add(rejecter_btn)
    send_markup.add(not_btn)
    return send_markup


