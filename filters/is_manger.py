

from aiogram.types import Message
from aiogram.dispatcher.filters import BoundFilter
from data.config import PAYMENT_MANAGER

class IsManager(BoundFilter):
    async def check(self, message: Message):
        return message.from_user.id == PAYMENT_MANAGER