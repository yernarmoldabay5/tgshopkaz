
# from loader import dp, db, bot, payment_manager_id
# from filters import IsManager
# from handlers.user.cart import payment_cb
#
# @dp.callback_query_handler(IsManager(), payment_cb.filter(action='REJECTED'))
# @dp.callback_query_handler(IsManager(), payment_cb.filter(action='FULFILLED'))
# async def category_callback_handler(callback_data: dict):
#     action = callback_data['action']
#     rowid = callback_data['id']
#
#     idx = db.fetchone('SELECT * FROM orders WHERE ROWID=?', (rowid,))
#     db.query('''UPDATE orders order set buy_flag = ? where order.unique_id = ?''', (action, idx,))
#     print("Deal was made")

