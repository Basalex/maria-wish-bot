from aiogram import Dispatcher
from . import base, callbacks

def setup_routers(dp: Dispatcher):
    dp.include_router(base.router)
    dp.include_router(callbacks.router)
