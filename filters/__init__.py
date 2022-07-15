from aiogram import Dispatcher
from .is_admin import IsAdmin
from .is_user import IsUser
from .is_manger import IsManager

def setup(dp: Dispatcher):
    dp.filters_factory.bind(IsAdmin, event_handlers=[dp.message_handlers])
    dp.filters_factory.bind(IsUser, event_handlers=[dp.message_handlers])
    dp.filters_factory.bind(IsManager, event_handlers=[dp.message_handlers])
