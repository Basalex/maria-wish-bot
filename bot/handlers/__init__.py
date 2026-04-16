from aiogram import Dispatcher
from . import base

def setup_routers(dp: Dispatcher):
    dp.include_router(base.router)
