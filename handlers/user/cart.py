import logging
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.products_from_cart import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from aiogram.types.chat import ChatActions
from states import CheckoutState
from loader import dp, db, bot, payment_manager_id
from filters import IsUser, IsManager
from .menu import cart

payment_cb = CallbackData('payment', 'id', 'chat_id', 'action')

@dp.message_handler(IsUser(), text=cart)
async def process_cart(message: Message, state: FSMContext):

    cart_data = db.fetchall(
        'SELECT * FROM cart WHERE cid=?', (message.chat.id,))

    if len(cart_data) == 0:

        await message.answer('Сіздің корзинаңыз бос.')

    else:

        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        async with state.proxy() as data:
            data['products'] = {}

        order_cost = 0

        for _, idx, count_in_cart in cart_data:

            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))

            if product == None:

                db.query('DELETE FROM cart WHERE idx=?', (idx,))

            else:
                _, title, body, image, price, _ = product
                order_cost += price

                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                markup = product_markup(idx, count_in_cart)
                text = f'<b>{title}</b>\n\n{body}\n\nБағасы: {price}₸.'

                await message.answer_photo(photo=image,
                                           caption=text,
                                           reply_markup=markup)

        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('📦 Сатып алу')

            await message.answer('Сатып алуға өту?',
                                 reply_markup=markup)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='count'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
async def product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    idx = callback_data['id']
    action = callback_data['action']

    if 'count' == action:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                await query.answer('Саны - ' + data['products'][idx][2])

    else:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                data['products'][idx][2] += 1 if 'increase' == action else -1
                count_in_cart = data['products'][idx][2]

                if count_in_cart == 0:

                    db.query('''DELETE FROM cart
                    WHERE cid = ? AND idx = ?''', (query.message.chat.id, idx))

                    await query.message.delete()
                else:

                    db.query('''UPDATE cart 
                    SET quantity = ? 
                    WHERE cid = ? AND idx = ?''', (count_in_cart, query.message.chat.id, idx))

                    await query.message.edit_reply_markup(product_markup(idx, count_in_cart))


@dp.message_handler(IsUser(), text='📦 Сатып алу')
async def process_checkout(message: Message, state: FSMContext):

    await CheckoutState.check_cart.set()
    await checkout(message, state)


async def checkout(message, state):
    answer = ''
    total_price = 0

    async with state.proxy() as data:

        for title, price, count_in_cart in data['products'].values():

            tp = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {tp}₽\n'
            total_price += tp

    await message.answer(f'{answer}\nТапсырыстың барлық сомасы: {total_price}₸.',
                         reply_markup=check_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [all_right_message, back_message], state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message):
    await message.reply('Бұндай нұсқа болған жоқ.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    await process_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message, state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await CheckoutState.next()
    await message.answer('Аты жөніңізді енгізіңіз.',
                         reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


@dp.message_handler(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):

    async with state.proxy() as data:

        data['name'] = message.text

        if 'address' in data.keys():

            await confirm(message)
            await CheckoutState.confirm.set()

        else:

            await CheckoutState.number.set()
            await message.answer('Телефон нөміріңізді енгізіңіз.',
                                 reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):

    async with state.proxy() as data:

        await message.answer('Аты-жөнін <b>' + data['name'] + '</b> осы нұсқадан ауыстыру?',
                             reply_markup=back_markup())

    await CheckoutState.name.set()


@dp.message_handler(IsUser(), state=CheckoutState.number)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['number'] = message.text

    await CheckoutState.address.set()
    await message.answer('Мекен-жайыңызды енгізіңіз.',
                         reply_markup=back_markup())

@dp.message_handler(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message):

    await message.answer('Барлық ақпарат дұрыс екеніне көз жеткізіп, тапсырысты растаңыз!',
                         reply_markup=confirm_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [confirm_message, back_message], state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message):
    await message.reply('Бұндай нұсқа болған жоқ.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    await CheckoutState.address.set()

    async with state.proxy() as data:
        await message.answer('Мекен-жайды <b>' + data['address'] + '</b> осы нұсқадан ауыстыру?',
                             reply_markup=back_markup())


@dp.message_handler(IsUser(), text=confirm_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    enough_money = True  # enough money on the balance sheet
    markup = ReplyKeyboardRemove()



    if enough_money:

        logging.info('Deal was made.')

        async with state.proxy() as data:

            cid = message.chat.id
            uid = get_unique_id()
            products = [idx + '=' + str(quantity)
                        for idx, quantity in db.fetchall('''SELECT idx, quantity FROM cart
            WHERE cid=?''', (cid,))]  # idx=quantity

            db.query('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (uid, cid, data['name'], data['number'], data['address'], ' '.join(products), 'IN_PROGRESS'))

            db.query('DELETE FROM cart WHERE cid=?', (cid,))

            rowid = db.fetchone('SELECT ROWID FROM orders WHERE unique_id=?', (uid,))
            print(type(rowid))
            await message.answer('Тапсырыс жасағаныңызға алғысымыз шексіз! Сізбен біздің менеджер байланысқа шығып төлем мәселесін талқылайтын болады!  🚀\nАты-жөні: <b>' + data['name'] + '</b>\nТел. нөмір: <b>' + data['number'] + '</b>\nАдрес: <b>' + data['address'] + '</b>',
                                 reply_markup=markup)
            await bot.send_message(payment_manager_id,'🚀\nАты-жөні: <b>' + data['name'] + '</b>\nНомер: <b>' + data['number'] + '</b>\nАдрес: <b>' + data['address'] + '</b>',
                                   reply_markup=construct_payment_manager_markup(rowid[0], cid))



    else:

        await message.answer('У вас недостаточно денег на счете. Пополните баланс!',
                             reply_markup=markup)

    await state.finish()


@dp.callback_query_handler(IsManager(), payment_cb.filter(action='REJECTED'))
@dp.callback_query_handler(IsManager(), payment_cb.filter(action='FULFILLED'))
async def payment_callback_handler(query: CallbackQuery, callback_data: dict):
    action = callback_data['action']
    rowid = callback_data['id']
    chat_id = callback_data['chat_id']

    # print(action)
    # print(type(rowid))
    # idx = db.fetchone("SELECT unique_id FROM orders WHERE ROWID= " + "'" + rowid[0] + "'" )
    #
    # print(idx)
    #db.query('UPDATE orders set buy_flag = ? where unique_id = ?', (action, idx,))
    db.query("UPDATE orders set buy_flag = " + "'" + action + "'" + " where ROWID = " + str(rowid))
    print("Deal was made")
    await query.message.delete()

    if action == 'FULFILLED':
        await bot.send_message(chat_id, 'Менеджер төлемді қабылдады,күтіңіз! Бізбен болғаныңызға рахмет 🧡', reply_markup=ReplyKeyboardRemove())
    else:
        await bot.send_message(chat_id, 'Сіз төлемнен бас тарттыңыз, бұл ұсыныс тек сіз үшін арналған еді.', reply_markup=ReplyKeyboardRemove())

def construct_payment_manager_markup(idx, cid):
    payment_manager_markup = InlineKeyboardMarkup()
    confirm_btn = InlineKeyboardButton('✅Төлем қабылданды', callback_data=payment_cb.new(id=idx, chat_id=cid, action='FULFILLED'))
    reject_btn = InlineKeyboardButton('🚫Клиент төлеуден бас тартты', callback_data=payment_cb.new(id=idx, chat_id=cid, action='REJECTED'))
    payment_manager_markup.add(confirm_btn, reject_btn)
    return payment_manager_markup

def get_unique_id():
    from datetime import datetime
    from uuid import uuid4

    eventid = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())
    return eventid